from rest_framework import serializers
from .models import Booking, FrontWebsiteEnquiry, VisaCountry, VisaCategory


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = "__all__"


class VisaCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisaCountry
        fields = [
            "id",
            "country",
        ]  # Assuming you want to include all fields, adjust as needed


class VisaCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VisaCategory
        fields = ["id", "category"]


class FrontWebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrontWebsiteEnquiry
        fields = ['name','email','phone','country_name','category_name','message','image']
