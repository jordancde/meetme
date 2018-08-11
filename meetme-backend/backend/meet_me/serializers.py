from rest_framework import serializers
from .models import MeetMeUser, Slot, Request, Meeting

# first we define the serializers

class MeetMeUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetMeUser
        fields = '__all__'
        #fields = ("user", "slots", "requests","meetings")

class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = '__all__'
        #fields = ("user", "slots", "requests","meetings")

class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = '__all__'
        #fields = ("user", "slots", "requests","meetings")

class MeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = '__all__'
        #fields = ("user", "slots", "requests","meetings")
