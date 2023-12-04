
from django.urls import path , include
# from .AdminViews import *
from .AgentViews import *


urlpatterns = [
    
    # path('Dashboard/', TemplateView.as_view(template_name='Agent/Base/index2.html'), name='agent_dashboard'),
    path('Dashboard',agent_dashboard.as_view(),name="agent_dashboard"),
    path('Login/', agent_login,name="agent_login"),
    
    path('Agent/AddLeads/', AgentEnquiryCreateView.as_view(),name="Agent_add_leads"),
    path('Agent/AllLeads/', agent_leads,name="agent_leads"),
    path('Agent/lead_enquiry/',lead_enquiry,name="Agent_lead_enquiry"),

    path('Agent/AppointmentList/',appointment_list.as_view(),name="Agent_appointment_list"),
    path('Agent/logout', agent_logout,name="agent_logout"),
    
    path('Agent/Addfaq/', FAQCreateView.as_view(),name="Agent_addfaq"),
    path('Agent/faqMaster/', FAQListView.as_view(),name="Agent_faqlist"),
    path('Agent/faqEdit/<int:pk>', FAQUpdateView.as_view(),name="Agent_edit_faq"),
    path('Agent/faq/delete/<int:id>/', delete_faq, name='Agent_delete_faq'),
    
    
    path('Agent/EnrolledApplication',enrolled_Application.as_view(),name="Agent_enroll_application"),
    path('Agent/WorkExperience/<int:id>',workexperience,name="Agent_workexperience"),
    path('Agent/edit/Enrolled/Application/<int:id>',edit_enrolled_application,name="Agent_edit_enrolled_application"),
    path('Agent/Educaion/Summary/<int:id>',education_summary,name="Agent_education_summary"),
    path('Agent/Test/Score/<int:id>',test_score,name="Agent_test_score"),
    path('Agent/Test/Score/Delete/<int:id>',delete_test_score,name="Agent_delete_test_score"),
    path(
        "Agent/viewenrolledapplication/<int:pk>",
        EnrolledApplicationView.as_view(),
        name="Agent_viewenrolledapplication",
    ),
    
    
    path('Agent/Background/Infromation/<int:id>',background_information,name="Agent_background_information"),
    
    path('Agent/Uploaddocument/',upload_document,name="Agent_uploaddocument"),
    path('Agent/ViewEnquiryList/<int:id>',view_enqlist,name="Agent_view_enqlist"),
    path(
        "AgentDelete/UploadFile/<int:id>", agntdelete_docfile, name="agntdelete_docfile"
    ),
    
    path('Agent/profile',profileview.as_view(),name="Agent_profile"),
    path('Agent/edit_profile/', edit_profile, name='edit_agent_profile'),
    
    path("get_country_data/", get_country_data, name="Agent_get_country_data"),
    path("leads/details/<str:country_name>", leads_detail, name="Agent_leads_detail"),
    
    path("Agent/PackageList/", PackageListView.as_view(), name="Agent_Package_list"),
    
    path("leads/Packageenquiry/<int:id>", AgentPackageEnquiryCreateView.as_view(), name="Agent_package_enquiry"),
    
]