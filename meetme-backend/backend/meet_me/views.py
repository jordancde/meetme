import datetime

from django.contrib.auth.models import User, Group
from .models import MeetMeUser, Slot, Request, Meeting, MeetMeUser
from .serializers import MeetMeUserSerializer, SlotSerializer, RequestSerializer, MeetingSerializer

from django.views import View
from django.core.paginator import Paginator
from rest_framework import generics

from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status

from rest_framework.decorators import api_view

import dateutil.parser

class GenericList(generics.ListCreateAPIView):
    serializer_class = None
    Model = None
    queryset = None
    search_fields = []
    sort_by = None
    user_attribute = False

    user_attribute_name = None

    def list(self, request, *args, **kwargs):
        if(self.user_attribute):

            meet_user = MeetMeUser.objects.get(pk=request.user.pk)
            id_list = meet_user.get(self.user_attribute)

            self.queryset = get_user_models(self.Model,self.id_list)

        data = get_list(request,self.queryset.all(),self.serializer_class,self.search_fields)
        return Response(data,status=status.HTTP_200_OK)

    def post(self,request, *args, **kwargs):

        response = super(GenericList,self).post(request)

        if(user_attribute):
            id_list = getattr(request.user,self.user_attribute_name).split(",")
        id_list.append(response.data["id"])

        id_list = ','.join(id_list)

        setattr(request.user,self.user_attribute_name,id_list)
        request.user.save()

        return response


class GenericDetails(View):
    Model = None
    serializer_class = None
    user_attribute = False

    user_attribute_name = None
    
    def get(self, request, *args, **kwargs):
        return get_object(kwargs.get("pk"),self.Model,self.serializer_class)

    def delete(self, request, *args, **kwargs):

        if(self.user_attribute):
            id_list = getattr(request.user,self.user_attribute_name).split(",")
            id_list.remove(kwargs.get("pk"))
            id_list = ','.join(id_list)
            setattr(request.user,self.user_attribute_name,id_list)
            request.user.save()
       
        return delete_object(kwargs.get("pk"),self.Model)

    def patch(self, request, *args, **kwargs):
        return patch_object(request,kwargs.get("pk"),self.Model,self.serializer_class)


class MeetMeUserListView(GenericList):
    Model = MeetMeUser
    serializer_class = MeetMeUserSerializer
    queryset = MeetMeUser.objects.all()


class SlotsListView(GenericList):

    Model = Slot
    serializer_class = SlotSerializer
    user_attribute = True 
    user_attribute_name = "slots"

    def get(self, request, *args, **kwargs):
        tag = request.GET.get("tag")

        if(tag=="mutual"):

            requestee_slot_ids = MeetMeUser.objects.get(pk=kwargs.get("pk")).slots.split(",")
            requester_slot_ids = request.user.slots.split(",")

            if(len(requestee_slot_ids)>0):
                requestee_slots = Slot.objects.filter(pk__in=requestee_slot_ids).order_by("start")
            else:
                requestee_slots=[]

            if(len(requester_slot_ids)):
                requester_slots = Slot.objects.filter(pk__in=requester_slot_ids).order_by("start")
            else:
                requester_slots = []

            start = min(requestee_slots[0].start,requester_slots[0].start)
            end = max(requestee_slots[len(requestee_slots)-1].end,requester_slots[len(requester_slots)-1].end)
            #TODO
            print(start)
            print(end)
            #mutual_slots = get_mutual_slots(requestee_slots,requester_slots)

    def post(self, request, *args, **kwargs):
        start = dateutil.parser.parse(request.data["start"])
        end = dateutil.parser.parse(request.data["end"])
        user = MeetMeUser.objects.get(user=request.user.id)
        location = request.data["location"]
        tag = "open"
        #FIX
        slot_ids = list(filter(str.strip, user.slots.split(",")))
        user_slots = None
        if(len(slot_ids)>0):
            user_slots = Slot.objects.get(pk__in=slot_ids).order_by("start")  

        slot = Slot.objects.create(
            start = start,
            end = end,
            user = user,
            location = location,
            tag = tag
        )

        if(not user_slots or slots_overlap([slot],user_slots)):
            slot.delete()
            return Response(error_response(400,"Slot overlaps with existing slot"),status=status.HTTP_400_BAD_REQUEST)
        else:
            user.slots = ",".join(user.slots.split(",").append(slot.id))
            user.save()
            return Response(data=SlotSerializer(slot).data,status=status.HTTP_201_CREATED)


def slots_overlap(slots_one,slots_two):
    overlap = get_mutual_slots(slots_one,slots_two)
    for period in overlap:
        if period:
            return True
    
    return False

def get_mutual_slots(slots_one,slots_two):

    slots_one = slots_one.order_by("start")
    slots_two = slots_two.order_by("start")

    start = min(slots_one[0].start,slots_two[0].start)
    end = max(slots_one[len(slots_one)-1].end,slots_two[len(slots_two)-1].end)

    slots_one_array = get_period_array(slots_one,start,end)
    slots_two_array = get_period_array(slots_two,start,end)

    mutual_slots_array = [False] * len(slots_one_array)

    for i in range(0,len(slots_one_array)):
        mutual_slots_array = slots_one_array[i] and slots_two_array[i]
    
    return convert_periods_to_datetime(mutual_slots_array,start)
    
def convert_periods_to_datetime(periods,start):
    datetimes = []

    period_start = None
    period_end = None
    for i in range(0,len(periods)):
        if not period_start:
            period_start = start + datetime.timedelta(minutes=i)
        else:
            if not periods[i]:
                period_end = start + datetime.timedelta(minutes=i-1)
                datetimes.append({
                    "start":period_start,
                    "end": period_end
                })
                period_start = None
                period_end = None

    return datetimes


# converts list of timeslots to array of 1 min representative bytes
def get_period_array(slots,start,end):

    start = round_to_minute(start,False)
    end = round_to_minute(start,True)

    delta = end - start
    periods = delta.minutes
    array = [False] * periods

    for slot in slots:
        if(slot.end>start and slot.start<end):
            slot_start = slot.start if slot.start>start else start
            slot_end = slot.end if slot.end<end else end
            slot_delta = slot.end-slot.start
            slot_periods = slot_delta.minutes

            start_index = (slot_start-start)

            for i in range(start_index,slot_periods):
                array[i] = True
    
def round_to_minute(dt,round_up):
    dt_start_of_minute = dt.replace(second=0, microsecond=0)

    if round_up:
        # round up
        dt = dt_start_of_minute + datetime.timedelta(minutes=1)
    else:
        # round down
        dt = dt_start_of_minute

    return dt


class MeetingsListView(GenericList):
    serializer_class = MeetingSerializer
    Model = Meeting
    user_attribute = True 
    user_attribute_name = "meetings"

class RequestsListView(GenericList):
    serializer_class = RequestSerializer
    Model = Request
    user_attribute = True 
    user_attribute_name = "requests"


class MeetMeUserDetailsView(GenericDetails):
    Model = MeetMeUser
    serializer_class = MeetMeUserSerializer

class SlotsDetailsView(GenericDetails):
    Model = Slot
    serializer_class = SlotSerializer
    user_attribute = True 
    user_attribute_name = "slots"

class RequestsDetailsView(GenericDetails):
    Model = Request
    serializer_class = RequestSerializer
    user_attribute = True 
    user_attribute_name = "requests"

class MeetingsDetailsView(GenericDetails):
    Model = Meeting
    serializer_class = MeetingSerializer
    user_attribute = True 
    user_attribute_name = "meetings"

    def delete(self, request, *args, **kwargs):
        meeting = Meeting.objects.get(pk=kwargs.get("pk"))
        request_model = Request.objects.get(pk=meeting.request)
        request_model.status = False
        request_model.save()
        return super(MeetingsDetailsView,self).delete(request, args, kwargs)


class MeetMeUserDetails(View):
    #permission_classes = [permissions.IsAuthenticated, TokenHasReadWriteScope]
    queryset = MeetMeUser.objects.all()
    serializer_class = MeetMeUserSerializer


    

def get_user_models(Model,id_list):
    model_ids = id_list.split(",")
    queryset = []
    for model_id in model_ids:
        if Model.objects.filter(pk=model_id).count()>0:
            queryset.append(Model.objects.get(pk=model_id))

    return queryset

def get_list(request,queryset,Serializer, search_fields=None):

    tag = request.GET.get("tag",None)
    search = request.GET.get("search",None)
    limit = request.GET.get("limit",None)
    page = request.GET.get("page",None)
    sort = request.GET.get("sort",None)
    if(tag):
        queryset = queryset.filter(tag=tag)

    if(search):
        searchset = []
        for search_field in search_fields:
            for obj in queryset:
                if(obj.get(search_field)==search and not obj in searchset):
                    searchset.append(obj)
        queryset = searchset
    
    if(sort):
        queryset = queryset.order_by(sort)

    if(page and limit):
        p = Paginator(queryset, limit)
        models = p.page(page).object_list

        param_string = "/?limit="+str(limit)
        if(tag):
            param_string+="&tag="+tag
        if(search):
            param_string+="&search="+search

        data = {
            "data": Serializer(models, many=True).data,
            "links": []
        }

        if int(page) != 1:
            prev_page = {
                "href": param_string+"&page="+str(int(page)-1),
                "rel": "prev_page",
                "method": "GET"
            }
            data["links"].append(prev_page)

        if int(page) != p.num_pages:
            next_page = {
                "href": param_string+"&page="+str(int(page)+1),
                "rel": "next_page",
                "method": "GET"
            }
            data["links"].append(next_page)

        current_page = {
            "href": param_string+"&page="+str(page),
            "rel": "self",
            "method": "GET"
        }

        data["links"].append(current_page)

    else:
        data = Serializer(queryset, many=True).data
    
    return data


def get_object(pk, Model, Serializer, model=None):
    if(model):
        serializer = Serializer(model)
    else:
        try:
            model = Model.objects.get(pk=pk)
        except:
            return HttpResponse(error_response(404, "Asset does not exist"), status=status.HTTP_404_NOT_FOUND)

    serializer = Serializer(model)
    return HttpResponse(serializer.data, status=status.HTTP_200_OK)


def delete_object(pk, Django_Model):
    try:
        django_model = Django_Model.objects.get(pk=pk)
    except:
        return HttpResponse(error_response(404, "Does not exist"), status=status.HTTP_404_NOT_FOUND)

    django_model.delete()

    return HttpResponse(status=status.HTTP_204_NO_CONTENT)
  

def patch_object(request, pk, Django_Model, Serializer):
    try:
        django_model = Django_Model.objects.get(pk=pk)
    except:
        return HttpResponse(error_response(404, "does not exist"), status=status.HTTP_404_NOT_FOUND)

    model_list = Django_Model.objects.filter(pk=pk)

    for key, value in request.data.items():
        if(value==""or value==None): continue
        model_list.update(**{key: value})

    django_model = Django_Model.objects.get(pk=pk)
    return HttpResponse(Serializer(django_model).data, status=status.HTTP_200_OK)


def error_response(code, message):
    return {
        "code": code,
        "message": message
    }