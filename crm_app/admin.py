from django.contrib import admin
from .models import *

# Register your models here.
class CustomUserAdmin(admin.ModelAdmin):
    list_display=['email']
    
class EnquiryAdmin(admin.ModelAdmin):
    list_display=['enquiry_number']   
    

admin.site.register(CustomUser,CustomUserAdmin)
admin.site.register(VisaCountry)
admin.site.register(VisaCategory)
admin.site.register(VisaSubcategory)
admin.site.register(CourierAddress)
admin.site.register(CaseStatus)
admin.site.register(followuppayment_status)
admin.site.register(followup_status)
admin.site.register(followupType)
admin.site.register(DocumentCategory)
admin.site.register(Currency)
admin.site.register(Document)
admin.site.register(SuccessStories)
admin.site.register(News)
admin.site.register(OfferBanner)
admin.site.register(Package)
admin.site.register(CaseCategoryDocument)
#admin.site.register(Employee,EmployeeAdmin)
admin.site.register(FrontWebsiteEnquiry)
admin.site.register(Enquiry,EnquiryAdmin)
#admin.site.register(Agent)
admin.site.register(LoginLog)
admin.site.register(Department)
admin.site.register(Group)
admin.site.register(Notes)
admin.site.register(Education_Summary)
admin.site.register(TestScore)
admin.site.register(Background_Information)
admin.site.register(ApplicationDocuments)
admin.site.register(OutSourcingAgent)
admin.site.register(ApplicationStatus)
admin.site.register(AssignRoles)
admin.site.register(Menu)
admin.site.register(Branch)
admin.site.register(AgentAgreement)
admin.site.register(PackageImage)
admin.site.register(FAQ)
admin.site.register(FollowUp)
admin.site.register(ActivityLog)
admin.site.register(Booking)
admin.site.register(ChatMessage)



class MemberAdmin(admin.ModelAdmin):
    list_display=('get_user_first_name','get_user_last_name','get_user_email',"department",'contact_no')

    def get_user_first_name(self, obj):
        return obj.users.first_name
    get_user_first_name.short_description = 'First Name'

    def get_user_last_name(self, obj):
        return obj.users.last_name
    get_user_last_name.short_description = 'Last Name'

    def get_user_email(self, obj):
        return obj.users.email
    get_user_email.short_description = 'Email'


admin.site.register(Admin,MemberAdmin)


class EmployeeAdmin(admin.ModelAdmin):
    list_display = "users", "contact_no"


admin.site.register(Employee, EmployeeAdmin)




class AgentAdmin(admin.ModelAdmin):
    list_display = "users", "contact_no"


admin.site.register(Agent, AgentAdmin)



