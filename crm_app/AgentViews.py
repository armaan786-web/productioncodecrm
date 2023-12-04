from django.views.generic import CreateView , ListView , UpdateView , DetailView , TemplateView
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,logout, login as auth_login
from django.http import HttpResponse, HttpResponseRedirect
from .models import *
from .forms import EnquiryForm,FAQForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.decorators import login_required
import calendar
from django.db.models import Prefetch
from django.db.models.functions import TruncMonth
import requests
from django.http import JsonResponse


class agent_dashboard(TemplateView):
    template_name = "Agent/Base/index2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        
        agent_count = Agent.objects.filter(registerdby=self.request.user).count()
        
        outsourceagent_count = OutSourcingAgent.objects.filter(
            registerdby=self.request.user
        ).count()

        
        user = CustomUser.objects.all()
        logged_in_users = CustomUser.objects.filter(is_logged_in="True")

       
        leadaccept_count = Enquiry.objects.filter(
            lead_status="Enrolled", created_by=self.request.user
        ).count()
        
        lead_count = Enquiry.objects.filter(
            created_by=self.request.user
        ).count()
        
        enquiry = (
            Enquiry.objects.filter(created_by=self.request.user)
            .exclude(lead_status__in=["New Lead", "Active"])
            .order_by("-last_updated_on")[:10]
        )
        
        package = Package.objects.all().order_by("-last_updated_on")[:10]

        enquiry_data = Enquiry.objects.values("Visa_country__country").annotate(
            count=Count("id")
        )

        labels = [item["Visa_country__country"] for item in enquiry_data]
        data = [item["count"] for item in enquiry_data]
        users = self.request.user

        labels = [item["Visa_country__country"] for item in enquiry_data]
        data = [item["count"] for item in enquiry_data]
        users = self.request.user
        if users.user_type == "4":
            user_enq = Enquiry.objects.filter(assign_to_agent=self.request.user.agent)
        else:
            user_enq = Enquiry.objects.filter(
                assign_to_outsourcingagent=self.request.user.outsourcingagent
            )
        
        monthly_counts = (
            user_enq.annotate(month=TruncMonth("registered_on"))
            .values("month")
            .annotate(count=Count("id"))
        )
        monthly_labels = [entry["month"].strftime("%B %Y") for entry in monthly_counts]
        monthly_count = [entry["count"] for entry in monthly_counts]
        
        user = self.request.user
        if user.user_type == "4":
            agent = Agent.objects.get(users=user)
            context['agent'] = agent
            
        if user.user_type == "5":
            outagent = OutSourcingAgent.objects.get(users=user)
            context['agent'] = outagent

        

        context["agent_count"] = agent_count
        context["outsourceagent_count"] = outsourceagent_count
        context["leadaccept_count"] = leadaccept_count
        context['lead_count'] = lead_count
        context["user"] = user
        context["enquiry"] = enquiry
        context["package"] = package
        context["logged_in_users"] = logged_in_users
        context["labels"] = labels
        context["data"] = data

        context["monthly_labels"] = monthly_labels
        context["monthly_count"] = monthly_count
        return context

    def get_month_name(self, month):
        return datetime(2023, month, 1).strftime("%b")
        
        
def get_country_data(request):
    user = request.user

    country_data = (
        Enquiry.objects.filter(created_by=user)
        .values("Visa_country__country")
        .annotate(total_inquiries=Count("id"))
    )

    country_data_list = list(country_data)

    return JsonResponse(country_data_list, safe=False)

@login_required
def leads_detail(request, country_name):
    users = request.user

    enquiry = Enquiry.objects.filter(
        created_by=users, Visa_country__country=country_name
    )
    
    context = {"enq": enquiry}
    return render(request, "Agent/CountryWiseLeads/enquiry_list.html", context)



def agent_login(request):
    error_message = None  # Initialize the error message as None

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user_type = request.POST.get('type')
        print("type", user_type, username, password)

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if (user_type == "Agent" and user.user_type == "4") or (user_type == "OutSourcing Agent" and user.user_type == "5"):
                auth_login(request, user)
                print("Logged in successfully")
                return redirect('agent_dashboard')  # Redirect to the common dashboard
            else:
                error_message = "User type and user do not match."
        else:
            error_message = "Username or password is incorrect."

    return render(request, 'Agent/LoginPage/newlogin.html', {'error_message': error_message})

class AgentEnquiryCreateView(LoginRequiredMixin,CreateView):

    model = Enquiry
    form_class = EnquiryForm
    template_name = 'Agent/Leads/addenquiry.html'
    success_url = reverse_lazy('Agent_enroll_application') 
    
    def form_valid(self, form):
        user = self.request.user

        if user.user_type == "4":
            form.instance.assign_to_agent = user.agent
        elif user.user_type == "5":
            form.instance.assign_to_outsourcingagent = user.outsourcingagent

        form.instance.created_by = user
        form.instance.lead_status = "Enrolled"

        messages.success(self.request, 'Enquiry Added Successfully.')
        return super().form_valid(form)
 

@login_required
def agent_leads(request):
    user = request.user
    created_enq = Enquiry.objects.filter(created_by=user)
    if user.is_authenticated:
        
        if user.user_type == '4':
            
            enq = Enquiry.objects.filter(assign_to_agent=user.agent)
        elif user.user_type == '5':
            
            enq = Enquiry.objects.filter(assign_to_outsourcingagent=user.outsourcingagent)
        else:
            
            enq = None
        combined_enq = enq | created_enq
        print("enquiry", combined_enq)

        return render(request, 'Agent/Leads/leads.html', {'enq': combined_enq})

@login_required
def agent_logout(request):
    logout(request)
    return redirect("/")

  
class appointment_list(LoginRequiredMixin,ListView):
    model = Appointment
    template_name = 'Agent/Appointment/appointmentlist.html'
    context_object_name = 'appointment'
    
    
class FAQCreateView(LoginRequiredMixin,CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'Agent/FAQ/addfaq.html'
    success_url = reverse_lazy('Agent_faqlist') 
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        messages.success(self.request, 'FAQ Added Successfully.')
          
        return super().form_valid(form)
    
class FAQListView(LoginRequiredMixin,ListView):
    model = FAQ
    template_name = 'Agent/FAQ/faqlist.html'
    context_object_name = 'FAQs'

class FAQUpdateView(LoginRequiredMixin,UpdateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'Agent/FAQ/updatefaq.html'  
    success_url = reverse_lazy('Agent_faqlist')

    def form_valid(self, form):

        # Display a success message
        messages.success(self.request, 'FAQ updated successfully.')

        return super().form_valid(form)
   
@login_required 
def delete_faq(request, id):
    faq = get_object_or_404(FAQ, id=id)
    faq.delete()
    return redirect('Agent_faqlist')


class enrolled_Application(LoginRequiredMixin,ListView):
    model = Enquiry
    template_name = (
        "Agent/EnrolledApplication/enrolledapplicationlist.html"
    )
    context_object_name = "enquiry"

    def get_queryset(self):
        user = self.request.user
        return Enquiry.objects.filter(
            Q(created_by=user) &
            Q(lead_status="Enrolled")
            
        ).order_by("-id")

    def get_context_data(self, **kwargs):
        # Get the default context data (data from the Enquiry model)
        context = super().get_context_data(**kwargs)

        current_datetime = timezone.now()
        context["current_datetime"] = current_datetime

        # Add data from the Notes model to the context
        context["notes"] = Notes.objects.all()
        context["notes_first"] = Notes.objects.order_by("-id").first()
        # context['employee'] = Employee.objects.all()
        
        context["enqenrolled"] = Enquiry.objects.filter(lead_status="Enrolled")

        # employee_queryset = Employee.objects.all()

        return context
      
@login_required
def education_summary(request, id):
    try:
        enquiry = Enquiry.objects.get(id=id)
        # education_summary = Education_Summary.objects.get(enquiry_id=enquiry)
        if Education_Summary.objects.filter(enquiry_id=enquiry).exists():
            education_summary = Education_Summary.objects.get(enquiry_id=enquiry)
        else:
            # Handle the case where there is no matching Education_Summary
            education_summary = None

        if request.method == "POST":
            enq_id = request.POST.get("enq_id")
            educationcountry = request.POST.get("educationcountry")
            highest_education = request.POST.get("highest_education")
            gradingscheme = request.POST.get("gradingscheme")
            gradeaverage = request.POST.get("gradeaverage")
            recent_college = request.POST.get("recent_college")
            level_education = request.POST.get("level_education")
            institutecountry = request.POST.get("institutecountry")
            institutename = request.POST.get("institutename")
            instructionlanguage = request.POST.get("instructionlanguage")
            institutionfrom = request.POST.get("institutionfrom")
            institutionto = request.POST.get("institutionto")
            degreeawarded = request.POST.get("degreeawarded")
            degreeawardedon = request.POST.get("degreeawardedon")
            address = request.POST.get("address")
            city = request.POST.get("city")
            province = request.POST.get("province")
            zipcode = request.POST.get("zipcode")

            # education_summary = Education_Summary.objects.get(enquiry_id=enq_id)
            # education_summary, created = Education_Summary.objects.get_or_create(enquiry_id=enq_id)
            enquiry = get_object_or_404(Enquiry, id=enq_id)
            education_summary, created = Education_Summary.objects.get_or_create(
                enquiry_id=enquiry
            )
            education_summary.country_of_education = educationcountry
            education_summary.highest_level_education = highest_education
            education_summary.grading_scheme = gradingscheme
            education_summary.grade_avg = gradeaverage
            education_summary.recent_college = recent_college
            education_summary.level_education = level_education
            education_summary.country_of_institution = institutecountry
            education_summary.name_of_institution = institutename
            education_summary.primary_language = instructionlanguage
            education_summary.institution_from = institutionfrom
            education_summary.institution_to = institutionto
            education_summary.degree_Awarded = degreeawarded
            education_summary.degree_Awarded_On = degreeawardedon
            education_summary.Address = address
            education_summary.city = city
            education_summary.Province = province
            education_summary.zipcode = zipcode
            # education_summary.primary_language = institutecountry

            education_summary.save()
            return redirect("Agent_education_summary", id=id)

            # education_summary = Education_Summary.objects.create(enquiry_id=enq_id,country_of_education=educationcountry,highest_level_education=highest_education,grading_scheme=gradingscheme,grade_avg=gradeaverage,recent_college=recent_college)
        context = {"enquiry": enquiry, "Agent_education_summary": education_summary}
        return render(
            request,
            "Agent/EnrolledApplication/Subforms/education-form.html",
            context,
        )
    except Exception as e:
        # Print the error message to the console
        print("An error occurred:", e)



@login_required
def test_score(request, id):
    enquiry_id = Enquiry.objects.get(id=id)
    test_score = TestScore.objects.filter(enquiry_id=enquiry_id)
    

    if request.method == "POST":
        examtype = request.POST.get("examtype")
        examdate = request.POST.get("examdate")
        reading = request.POST.get("reading")
        listening = request.POST.get("listening")
        speaking = request.POST.get("speaking")
        writing = request.POST.get("writing")
        overallscore = request.POST.get("overallscore")

        # Check if a TestScore with the specified exam_type already exists
        existing_test_score = TestScore.objects.filter(exam_type=examtype,enquiry_id=enquiry_id).first()

        if existing_test_score is None:
            # If no TestScore with the specified exam_type exists, create a new one
            testScore = TestScore.objects.create(
                enquiry_id=enquiry_id,
                exam_type=examtype,
                exam_date=examdate,
                reading=reading,
                listening=listening,
                speaking=speaking,
                writing=writing,
                overall_score=overallscore,
            )
            testScore.save()
        else:
            # If an existing TestScore with the same exam_type is found, update it
            existing_test_score.exam_date = examdate
            existing_test_score.reading = reading
            existing_test_score.listening = listening
            existing_test_score.speaking = speaking
            existing_test_score.writing = writing
            existing_test_score.overall_score = overallscore
            existing_test_score.save()

        return redirect("Agent_test_score", id=id)

    context = {
        "test_score": test_score,
        "enquiry_id": enquiry_id,
    }
    

    return render(
        request,
        "Agent/EnrolledApplication/Subforms/test-score-form.html",
        context,
    )



@login_required
def delete_test_score(request, id):
    test_score = TestScore.objects.get(id=id)
    enquiry_id = test_score.enquiry_id.id
    test_score.delete()
    return redirect("Agent_test_score", id=enquiry_id)
    # print("sssss",test_score)



@login_required
def background_information(request, id):
    enquiry_id = Enquiry.objects.get(id=id)

    try:
        # Try to retrieve an existing Background_Information entry for this enquiry

        bk_info = Background_Information.objects.get(enquiry_id=enquiry_id)

        if request.method == "POST":
            exaustralliabeforeamtype = request.POST.get("australliabefore")

            # Update the existing Background_Information entry
            bk_info.background_information = exaustralliabeforeamtype
            bk_info.save()

            return redirect("Agent_background_information", id=id)
    except Background_Information.DoesNotExist:
        # If no existing entry is found, create a new one
        bk_info = None

        if request.method == "POST":
            exaustralliabeforeamtype = request.POST.get("australliabefore")

            # Create a new Background_Information entry
            bk_info = Background_Information.objects.create(
                enquiry_id=enquiry_id,
                background_information=exaustralliabeforeamtype,
            )

            return redirect("Agent_background_information", id=id)

    context = {
        "bk_info": bk_info,
        "enquiry_id": enquiry_id,
    }
    return render(
        request,
        "Agent/EnrolledApplication/Subforms/background-form.html",
        context,
    )

@login_required
def workexperience(request, id):
    enquiry_id = Enquiry.objects.get(id=id)

    try:
        # Try to retrieve an existing Background_Information entry for this enquiry

        work_exp = Work_Experience.objects.get(enquiry_id=enquiry_id)

        if request.method == "POST":
            companyname = request.POST.get("companyname")
            designation = request.POST.get("designation")
            fromdate = request.POST.get("fromdate")
            todate = request.POST.get("todate")
            address = request.POST.get("address")
            city = request.POST.get("city")
            state = request.POST.get("state")
            workdetails = request.POST.get("workdetails")

            # Update the existing Background_Information entry
            work_exp.company_name = companyname
            work_exp.designation = designation
            work_exp.from_date = fromdate
            work_exp.to_date = todate
            work_exp.address = address
            work_exp.city = city
            work_exp.state = state
            work_exp.describe = workdetails

            work_exp.save()

            return redirect("Agent_workexperience", id=id)
    except Work_Experience.DoesNotExist:
        # If no existing entry is found, create a new one
        work_exp = None

        if request.method == "POST":
            companyname = request.POST.get("companyname")
            designation = request.POST.get("designation")
            fromdate = request.POST.get("fromdate")
            todate = request.POST.get("todate")
            address = request.POST.get("address")
            city = request.POST.get("city")
            state = request.POST.get("state")
            workdetails = request.POST.get("workdetails")

            # Create a new Background_Information entry
            work_expc = Work_Experience.objects.create(
                enquiry_id=enquiry_id,
                company_name=companyname,
                designation=designation,
                from_date=fromdate,
                to_date=todate,
                address=address,
                city=city,
                state=state,
                describe=workdetails,
            )
            work_expc.save()

            return redirect("Agent_workexperience", id=id)

    context = {
        "enquiry_id": enquiry_id,
        "work_exp": work_exp,
    }
    return render(
        request,
        "Agent/EnrolledApplication/Subforms/workexperience-form.html",
        context,
    )

@login_required
def edit_enrolled_application(request, id):
    enquiry = Enquiry.objects.get(id=id)
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()
    subcategory = VisaSubcategory.objects.all()
    context = {
        "enquiry": enquiry,
        "country": country,
        "category": category,
        "subcategory": subcategory,
    }

    if request.method == "POST":
        title = request.POST.get("title")
        firstname = request.POST.get("firstname")
        middlename = request.POST.get("middlename")
        lastname = request.POST.get("lastname")
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        maritialstatus = request.POST.get("maritialstatus")
        source = request.POST.get("source")
        reference = request.POST.get("reference")
        visatype = request.POST.get("visatype")
        visacountry_id = request.POST.get("visacountry_id")
        visacategory_id = request.POST.get("visacategory_id")
        visasubcategory_id = request.POST.get("visasubcategory")
        digitalsignature = request.FILES.get("digitalsignature")
        spouse_name = request.POST.get("spouse_name")
        spouse_no = request.POST.get("spouse_no")
        spouse_email = request.POST.get("spouse_email")
        spouse_passport = request.POST.get("spouse_passport")
        spouse_dob = request.POST.get("spouse_dob")
        email = request.POST.get("email")
        mailing_phone = request.POST.get("mailing_phone")
        mailingCountry = request.POST.get("mailingCountry")
        mailingState = request.POST.get("mailingState")
        mailingCity = request.POST.get("mailingCity")
        mailingZipcode = request.POST.get("mailingZipcode")
        mailingAddress = request.POST.get("mailingAddress")
        permanentCountry = request.POST.get("permanentCountry")
        permanentState = request.POST.get("permanentState")
        permanentCity = request.POST.get("permanentCity")
        permanentZipcode = request.POST.get("permanentZipcode")
        permanentAddress = request.POST.get("permanentAddress")
        passportnumber = request.POST.get("passportnumber")
        issuedate = request.POST.get("issuedate")
        expirydate = request.POST.get("expirydate")
        issue_country = request.POST.get("issuecountry")
        birthcity = request.POST.get("birthcity")
        country_of_birth = request.POST.get("country_of_birth")
        nationality = request.POST.get("nationality")
        citizenship = request.POST.get("citizenships")
        more_than_one_country = request.POST.get("more_than_one_country")
        studyin_in_other_country = request.POST.get("studyin_in_other_country")

        citizenstatus = request.POST.get("citizenstatus")
        studystatus = request.POST.get("studystatus")

        citizen = request.POST.get("citizen")
        emergencyname = request.POST.get("emergencyname")
        emergencyphone = request.POST.get("emergencyphone")
        emergencyemail = request.POST.get("emergencyemail")
        applicantrelation = request.POST.get("applicantrelation")

        print("more_than_one_country.............", more_than_one_country)
        visa_country = VisaCountry.objects.get(id=visacountry_id)
        visa_category = VisaCategory.objects.get(id=visacategory_id)
        visa_subcategory = VisaCategory.objects.get(id=visacategory_id)

        enquiry.Salutation = title
        enquiry.FirstName = firstname
        enquiry.MiddleName = middlename
        enquiry.LastName = lastname
        enquiry.Dob = dob
        enquiry.Gender = gender
        enquiry.marital_status = maritialstatus
        enquiry.Source = source
        enquiry.Reference = reference
        enquiry.Visa_type = visatype
        enquiry.Visa_country = visa_country
        enquiry.Visa_category = visa_category
        enquiry.Visa_subcategory = visa_subcategory
        if digitalsignature:
            enquiry.digital_signature = digitalsignature
        enquiry.spouse_name = spouse_name
        enquiry.spouse_no = spouse_no
        enquiry.spouse_email = spouse_email
        enquiry.spouse_passport = spouse_passport
        enquiry.spouse_dob = spouse_dob
        enquiry.email = email
        enquiry.mailing_phone = mailing_phone
        enquiry.mailing_country = mailingCountry
        enquiry.state = mailingState
        enquiry.city = mailingCity
        enquiry.zipcode = mailingZipcode
        enquiry.address = mailingAddress
        enquiry.permanent_country = permanentCountry
        enquiry.permanent_state = permanentState
        enquiry.permanent_city = permanentCity
        enquiry.permanent_zipcode = permanentZipcode
        enquiry.permanent_address = permanentAddress
        enquiry.passport_no = passportnumber
        enquiry.issue_date = issuedate
        enquiry.expirty_Date = expirydate
        enquiry.issue_country = issue_country
        enquiry.city_of_birth = birthcity
        enquiry.country_of_birth = country_of_birth
        enquiry.nationality = nationality
        enquiry.citizenship = citizenship
        enquiry.more_than_one_country = more_than_one_country
        enquiry.studyin_in_other_country = studyin_in_other_country
        enquiry.emergency_name = emergencyname
        enquiry.emergency_phone = emergencyphone
        enquiry.emergency_email = emergencyemail
        enquiry.relation_With_applicant = applicantrelation
        enquiry.save()
        return redirect("Agent_edit_enrolled_application", id=id)

    return render(
        request,
        "Agent/EnrolledApplication/editenrolledapplication.html",
        context,
    )

class EnrolledApplicationView(LoginRequiredMixin,DetailView):
    model = Enquiry  
    template_name = "Agent/EnrolledApplication/viewenrolledapplication.html"
    context_object_name = "enq"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            
            enq = Enquiry.objects.get(pk=self.kwargs['pk'])
            context['enq'] = enq

            
            try:
                edu = Education_Summary.objects.get(enquiry_id=enq)
            except Education_Summary.DoesNotExist:
                edu = None  

            context['edu'] = edu
            
            try:
                back = Background_Information.objects.get(enquiry_id=enq)
            except Background_Information.DoesNotExist:
                back = None  

            context['back'] = back
            
            try:
                work = Work_Experience.objects.get(enquiry_id=enq)
            except Work_Experience.DoesNotExist:
                work = None  

            context['work'] = work

        except Enquiry.DoesNotExist:
            
            context['enq_not_found'] = True  

        return context
    
@login_required
def view_enqlist(request, id):
    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()

    # doc_file = DocumentFiles.objects.get(enquiry_id=enq)

    # try:
    doc_file = DocumentFiles.objects.filter(enquiry_id=enq)


    case_categories = CaseCategoryDocument.objects.filter(country=enq.Visa_country)

    # Create a Prefetch object to efficiently fetch related Document instances
    documents_prefetch = Prefetch(
        "document",
        queryset=Document.objects.select_related("document_category", "lastupdated_by"),
    )

    # Prefetch related Document instances and use the Prefetch object
    case_categories = case_categories.prefetch_related(documents_prefetch)

    # Create a dictionary to group documents by document_category
    grouped_documents = {}
    # demoo = {}
    # dddd = {}

    for case_category in case_categories:
        for document in case_category.document.all():
            document_category = document.document_category
            testing = document.document_category.id

            # demoo[xyz].append(dddd)

            if document_category not in grouped_documents:
                grouped_documents[document_category] = []

            grouped_documents[document_category].append(document)

    context = {
        "enq": enq,
        "grouped_documents": grouped_documents,
        "doc_file": doc_file,
    }
    print(context , enq.Visa_country , "Agent hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")

    return render(request, "Agent/Leads/viewenquiry.html", context)


def agntdelete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id
    

    doc_id.delete()
    return redirect("Agent_view_enqlist", enqq)

@login_required
def upload_document(request):
    if request.method == "POST":
        document_id = request.POST.get("document_id")
        enq_id = request.POST.get("enq_id")

        document = Document.objects.get(pk=document_id)
        document_file = request.FILES.get("document_file")
        enq = Enquiry.objects.get(id=enq_id)
        # Check if a DocumentFiles object with the same document exists
        try:
            doc = DocumentFiles.objects.filter(
                enquiry_id=enq_id, document_id=document
            ).first()
            if doc:
                
                doc.document_file = document_file
                doc.lastupdated_by = request.user
                doc.save()

                

                return redirect("Agent_view_enqlist", id=enq_id)
            else:
                

                documest_files = DocumentFiles.objects.create(
                    document_file=document_file,
                    document_id=document,
                    enquiry_id=enq,
                    lastupdated_by=request.user,
                )
                documest_files.save()
                return redirect("Agent_view_enqlist", id=enq_id)

        except Exception as e:
            pass
            
            
@login_required
def lead_enquiry(request):
    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        lead_status = request.POST.get('lead_status')

        
        
        try:
            enq = Enquiry.objects.get(id=enq_id)
            firstname = enq.FirstName
            lastname=enq.LastName
            mob =enq.contact
            enq_number = enq.enquiry_number
            if lastname:
              full_name = firstname + " " + lastname
            else:
                full_name = firstname 
        except Enquiry.DoesNotExist:
            # Handle the case where the Enquiry object is not found
            messages.error(request, 'Enquiry not found.')
            return redirect('agent_leads')
        enq.lead_status=lead_status
        enq.save()
        
        cast = lead_status + " for enquiry ID " + enq_number 
        
        url = "http://sms.txly.in/vb/apikey.php"
        payload = {
            "apikey": "lbwUbocDLNFjenpa",
            "senderid": "SKTRAL",
            "templateid": "1007184056708073105",
            "number": mob,
            "message": f"Hello {full_name} , Your lead status is updated {cast} for TheSkyTrails CRM. Thank You"
        }
        response = requests.post(url,data=payload)


    return redirect('agent_leads')


class profileview(TemplateView,LoginRequiredMixin):
    template_name = "Agent/profile.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = Enquiry.objects.filter(created_by=self.request.user)
        
        user = self.request.user
        if user.user_type == "4":
            agent = Agent.objects.get(users=user)
            context['agent'] = agent
            
        if user.user_type == "5":
            outagent = OutSourcingAgent.objects.get(users=user)
            context['agent'] = outagent
            
            
        if hasattr(user, 'get_user_type_display'):
            context['user_type'] = user.get_user_type_display()
        context['leads'] = leads
        

        return context
    
    
@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')

        if user.agent.type == "Agent":
            agent_instance = Agent.objects.get(users=request.user)
            
            agent_instance.users.first_name = first_name
            agent_instance.users.last_name = last_name
            agent_instance.users.email = email
            agent_instance.contact_no = contact

            
            agent_instance.users.save()
            agent_instance.save()
        
        elif user.agent.type == "Outsourcing Partner":
            
            outsource_instance = OutSourcingAgent.objects.get(users=request.user)
            
            outsource_instance.users.first_name = first_name
            outsource_instance.users.last_name = last_name
            outsource_instance.users.email = email
            outsource_instance.contact_no = contact

            
            outsource_instance.users.save()
            outsource_instance.save()

        
        return redirect("Agent_profile")
        

    return render(request, 'Agent/profile.html')

  
    
    
class PackageListView(LoginRequiredMixin, ListView):
    model = Package
    template_name = "Agent/Package/packagelist.html"
    context_object_name = "Package"

    def get_queryset(self):
        return Package.objects.order_by("-id")
        
        
class AgentPackageEnquiryCreateView(LoginRequiredMixin, CreateView):
    model = Enquiry
    form_class = EnquiryForm
    template_name = 'Agent/Leads/packageenquiry.html'
    success_url = reverse_lazy('Agent_enroll_application') 

    def form_valid(self, form):
        user = self.request.user

        if user.user_type == "4":
            form.instance.assign_to_agent = user.agent
        elif user.user_type == "5":
            form.instance.assign_to_outsourcingagent = user.outsourcingagent

        form.instance.created_by = user
        form.instance.lead_status = "Enrolled"

        messages.success(self.request, 'Enquiry Added Successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the package_id from the URL parameters
        package_id = self.kwargs.get('id')
        
        # Add the selected package_id to the context
        context['package_id'] = package_id

        # Get all packages
        package = Package.objects.all()
        context['package'] = package

        return context


        
