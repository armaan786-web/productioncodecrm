from django.contrib.auth import authenticate,logout, login as auth_login
import requests
from datetime import date
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .models import *
from .forms import *
from django.views import View
from django.views.generic import CreateView , ListView , UpdateView , DetailView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest
from django.core.files.storage import FileSystemStorage
from .models import UploadedFile
import pandas as pd
from django.conf import settings
from django.http import JsonResponse
from django.http import HttpRequest
import calendar
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth


class employee_dashboard(TemplateView):
    template_name = "Employee/Base/index2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context["assigned_menus"] = assigned_menus

        # Count the total number of agents
        agent_count = Agent.objects.filter(registerdby=self.request.user).count()
        # Count the total number of outsource agents
        outsourceagent_count = OutSourcingAgent.objects.filter(
            registerdby=self.request.user
        ).count()

        # Count the total number of employees
        # employee_count = Employee.objects.count()
        user = CustomUser.objects.all()
        # current_user = self.request.user
        logged_in_users = CustomUser.objects.filter(is_logged_in="True")
        print("logged in user", logged_in_users)

        # print("is logged in",is_logged_in)

        # is_logged_in = LoginLog.objects.filter(user=current_user, logout_datetime=None).exists()
        # print("hellooo",logged_in_users)

        # Count the total number of employees
        leadpending_count = Enquiry.objects.filter(
            lead_status="Active", created_by=self.request.user
        ).count()
        leadaccept_count = Enquiry.objects.filter(
            lead_status="Enrolled", created_by=self.request.user
        ).count()
        leadreject_count = Enquiry.objects.filter(
            lead_status="New Lead", created_by=self.request.user
        ).count()
        leadcaseinitiated_count = Enquiry.objects.filter(
            lead_status="Case Initiated", created_by=self.request.user
        ).count()
        enquiry = (
            Enquiry.objects.filter(created_by=self.request.user)
            .exclude(lead_status__in=["New Lead", "Active"])
            .order_by("-last_updated_on")[:10]
        )
        new_lead = Enquiry.objects.filter(
            lead_status="Active", assign_to_employee=self.request.user.employee
        ).order_by("-last_updated_on")[:10]
        package = Package.objects.all().order_by("-last_updated_on")[:10]

        enquiry_data = Enquiry.objects.values("Visa_country__country").annotate(
            count=Count("id")
        )

       
        user_emp = Enquiry.objects.filter(assign_to_employee=self.request.user.employee)
        monthly_counts = (
            user_emp.annotate(month=TruncMonth("registered_on"))
            .values("month")
            .annotate(count=Count("id"))
        )
        labels = [entry["month"].strftime("%B %Y") for entry in monthly_counts]
        data = [entry["count"] for entry in monthly_counts]
        
        users = self.request.user

        

        now = datetime.now()
        follow_ups_today = FollowUp.objects.filter(
            created_by=self.request.user,
            calendar=now.date(),
            time__lte=(now + timedelta(minutes=5)).time(),  # Adjust as needed
        )

        context["agent_count"] = agent_count
        # context['employee_count'] = employee_count
        context["outsourceagent_count"] = outsourceagent_count
        context["leadpending_count"] = leadpending_count
        context["leadaccept_count"] = leadaccept_count
        context["leadreject_count"] = leadreject_count
        context["leadcaseinitiated_count"] = leadcaseinitiated_count
        context["user"] = user
        context["enquiry"] = enquiry
        context["new_lead"] = new_lead
        context["package"] = package

        context["logged_in_users"] = logged_in_users

        context["labels"] = labels
        context["data"] = data

        #context["monthly_labels"] = monthly_labels
        #context["monthly_count"] = monthly_count
        context["follow_ups_today"] = follow_ups_today
        return context

    def get_month_name(self, month):
        return datetime(2023, month, 1).strftime("%b")



@login_required
def employee_logout(request):
    logout(request)
    return redirect("/")

def employee_login(request):
    error_message = None  

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username, password)

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            
                auth_login(request, user)
                print("Logged in successfully")
                return redirect('employee_dashboard')  # Redirect to the common dashboard
        else:
            error_message = "Username or password is incorrect."

    return render(request, 'Employee/LoginPage/newlogin.html', {'error_message': error_message})


class EmployeeEnquiryCreateView(LoginRequiredMixin,CreateView):

    model = Enquiry
    form_class = EnquiryForm
    template_name = 'Employee/Leads/addenquiry.html'
    success_url = reverse_lazy('employee_leads') 
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.assign_to_employee = self.request.user.employee
        form.instance.lead_status = "Active"
        messages.success(self.request, 'Enquiry Added Successfully.')
        return super().form_valid(form) 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context


@login_required
def employee_leads(request):
    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    
    user = request.user
    created_enq = Enquiry.objects.filter(created_by=user).order_by("-id")
    if user.is_authenticated:
        # Check if the user is an Agent or Outsourcing Agent
        if user.user_type == '3':
            # If the user is an Agent, filter by assign_to_agent
            enq = Enquiry.objects.filter(Q(assign_to_employee=user.employee))
            print("helooooo",user)
        else:
            # Handle other user types as needed
            enq = None
        combined_enq = enq | created_enq


        context = {
        'assigned_menus': assigned_menus,
        'enq': combined_enq
    }

        

        return render(request, 'Employee/Leads/leads.html',context)


from django.db.models import Prefetch



@login_required
def viewemployee_enqlist(request, id):
    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)

    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()

    # try:
    doc_file = DocumentFiles.objects.filter(enquiry_id=enq)
    
    
    if request.method == "POST":
        follow_up_form = FollowUpForm(request.POST)
        if follow_up_form.is_valid():
            follow_up = follow_up_form.save(commit=False)
            follow_up.enquiry = enq
            follow_up.created_by = request.user
            follow_up.save()

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
        "assigned_menus": assigned_menus,
        "form": FollowUpForm(),
    }

    return render(request, "Employee/Leads/viewenquiry.html", context)


def emp_delete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id

    doc_id.delete()
    return redirect('viewemp_enqlist', enqq)
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

                return redirect("viewemp_enqlist", id=enq_id)
            else:
                documest_files = DocumentFiles.objects.create(
                    document_file=document_file,
                    document_id=document,
                    enquiry_id=enq,
                    lastupdated_by=request.user,
                )
                documest_files.save()
                return redirect("viewemp_enqlist", id=enq_id)

        except Exception as e:
            pass

from django.http import HttpResponse, FileResponse
@login_required
def download_document(request, document_id):
    # Retrieve the document
    doc = get_object_or_404(Document, id=document_id)

    # Create a response to trigger the file download
    response = FileResponse(doc.document_file)
    response['Content-Disposition'] = f'attachment; filename="{doc.document_file.name}"'
    return response

@login_required
def emp_lead_enquiry_update(request):
    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    context = {
        'assigned_menus': assigned_menus
    }

    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        lead_status = request.POST.get('lead_status')

        
        enq = Enquiry.objects.get(id=enq_id)
        
        firstname = enq.FirstName
        lastname=enq.LastName
        mob =enq.contact
        enq_number = enq.enquiry_number
        if lastname:
            full_name = firstname + " " + lastname
        else:
            full_name = firstname 
        
        if enq.lead_status == "Case Initiated":
            messages.warning(request,'Enquiry Status Not Updated As Visa Case Is Already Inititated.')
            return redirect('employee_leads')
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
        
        url = reverse('employee_leads')
    return redirect(url, assigned_menus=context)


@login_required
def employee_accept_leads(request):
    if request.method == "POST":
        accept = request.POST.get('accept')
        print("accepptt",accept)
        enq_id = request.POST.get('enq_id')
        enquiry = Enquiry.objects.get(id=enq_id)
        enquiry.lead_status = "Active"
        enquiry.assign_to_employee=request.user.employee
        enquiry.save()
        return redirect('employee_leads')
    
class MenuListView(LoginRequiredMixin,ListView):
    model = Menu
    template_name = 'Employee/Rolesmanagement/menulist.html'
    context_object_name = 'menu'
    
    def get_queryset(self):
        return Menu.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context


class AddMenu(LoginRequiredMixin,CreateView):
    model = Menu
    form_class = MenuForm
    template_name = 'Employee/Rolesmanagement/addmenu.html'
    success_url = reverse_lazy('Employee_Menu_list')  
    
    def form_valid(self, form):
        # Check if a menu item with the same name already exists
        name = form.cleaned_data['name']
        if Menu.objects.filter(name=name).exists():
            # Handle the case where the menu item already exists
            # You can add your custom logic here, such as showing an error message
            # or redirecting to a different page
            messages.warning(self.request, 'Menu item with this name already exists.')
            return redirect('Employee_add_menu')

        # If the menu item doesn't exist, proceed with saving it
        messages.success(self.request, 'Menu item has been successfully created.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context

class EditMenuView(LoginRequiredMixin, UpdateView):
    model = Menu
    form_class = MenuForm
    template_name = 'Employee/Rolesmanagement/menuupdate.html'
    success_url = reverse_lazy('Employee_Menu_list')

    def form_valid(self, form):
        # Check if a menu item with the same name already exists
        name = form.cleaned_data['name']
        menu_instance = self.get_object()

        if Menu.objects.exclude(pk=menu_instance.pk).filter(name=name).exists():
            # Handle the case where the menu item already exists
            # You can add your custom logic here, such as showing an error message
            # or redirecting to a different page
            messages.warning(self.request, 'Menu item with this name already exists.')
        else:
            # If the menu item doesn't exist, proceed with saving it
            messages.success(self.request, 'Menu item has been updated successfully.')
            response = super().form_valid(form)
            return redirect(self.get_success_url())

        # Redirect back to the form page
        return redirect(self.get_success_url())  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context   
    
@login_required   
def add_employee(request):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    

    departments = Department.objects.all()
    branches = Branch.objects.all()

    if request.method == "POST":
        department_id = request.POST.get('department_id')
        branch_id = request.POST.get('branch_id')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        password = request.POST.get('password')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        address = request.POST.get('address')
        zipcode = request.POST.get('zipcode')
        status = request.POST.get('status')
        files = request.FILES.get('file')

        # Ensure that branch_id is provided
        if not branch_id:
            messages.warning(request, 'Branch ID is required')
            return redirect('Employee_add_employee')

        try:
            department = Department.objects.get(id=department_id)
            branchh = Branch.objects.get(id=branch_id)
            user = CustomUser.objects.create_user(
                username=email, first_name=firstname, last_name=lastname, email=email, password=password, user_type='3'
            )
           
            user.employee.department = department
            user.employee.branch = branchh
            user.employee.contact_no = contact
            user.employee.country = country
            user.employee.state = state
            user.employee.City = city
            user.employee.Address = address
            user.employee.zipcode = zipcode
            user.employee.status = status
            user.employee.file = files
            user.save()
            messages.success(request, 'Employee Added Successfully!!')
            return redirect('Employee_all_employee')
        except Exception as e:
            messages.warning(request, str(e))
            return redirect('Employee_add_employee')

    context = {
        'department': departments,
        'branch': branches,
        'assigned_menus' : assigned_menus
    }
    return render(request, 'Employee/Employee/addemployee.html', context)


class all_employee(LoginRequiredMixin,ListView):
    model = Employee
    template_name = 'Employee/Employee/employeelist.html'  
    context_object_name = 'employee'
    
    def get_queryset(self):
        return Employee.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    

class view_employee(LoginRequiredMixin,ListView):
    model = Employee
    template_name = 'Employee/Employee/employeeview.html'  
    context_object_name = 'employee'
    
    def get_queryset(self):
        # Get the employee_id from the URL parameter
        employee_id = self.kwargs['employee_id']
        
        
        # Filter the queryset to get the employee with the specified ID
        queryset = Employee.objects.get(id=employee_id)
        
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
@login_required
def employee_update(request,pk):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    

    department = Department.objects.all()
    employee = Employee.objects.get(pk=pk)
    context = {
        'employee':employee,
        'department':department,
        'assigned_menus':assigned_menus
    }

    return render(request,'Employee/Employee/employeeupdate.html',context)
    
@login_required
def employee_update_save(request):
    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    context = {
        'assigned_menus': assigned_menus
    }
    if request.method == "POST":
        employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        address = request.POST.get('address')
        zipcode = request.POST.get('zipcode')
        status = request.POST.get('status')
        file = request.FILES.get('file')
        

        
        user = CustomUser.objects.get(id=employee_id)
       
        department = Department.objects.get(id=department_id)

        user.first_name= firstname
        user.last_name= lastname
        user.email= email

        user.employee.department= department
       
        user.employee.contact_no=contact
        user.employee.country= country
        user.employee.state= state
        user.employee.City= city
        user.employee.Address= address
        user.employee.zipcode= zipcode
        user.employee.status= status
        if file:
            user.employee.file= file
        user.save()
        messages.success(request,'Employee Updated Successfully')
        url = reverse('Employee_all_employee')
    return redirect(url, assigned_menus=context)
  
    
class SuccessStoriesCreateView(LoginRequiredMixin,CreateView):
    model = SuccessStories
    form_class = SuccessStoriesForm
    template_name = 'Employee/General/SuccessStories/addnewsuccessstory.html'
    success_url = reverse_lazy('Employee_SuccessStories_list')  
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        
        messages.success(self.request, 'SuccessStory Added Successfully.')
          
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
    
class SuccessStoriesListView(LoginRequiredMixin,ListView):
    model = SuccessStories
    template_name = 'Employee/General/SuccessStories/successstorieslist.html'  
    context_object_name = 'SuccessStories'
    
    def get_queryset(self):
        return SuccessStories.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context


class editSuccessStory(LoginRequiredMixin,UpdateView):
    model = SuccessStories
    form_class = SuccessStoriesForm
    template_name = 'Employee/General/SuccessStories/updatesuccessstory.html'
    success_url = reverse_lazy('Employee_SuccessStories_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'SuccessStory Updated Successfully.')

        return super().form_valid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
class NewsCreateView(LoginRequiredMixin,CreateView):
    model = News
    form_class = NewsForm
    template_name = 'Employee/General/News/addnews.html'
    success_url = reverse_lazy('Employee_News_list')  
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        
        messages.success(self.request, 'News Added Successfully.')
          
        return super().form_valid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
    
class NewsListView(LoginRequiredMixin,ListView):
    model = News
    template_name = 'Employee/General/News/newslist.html'  
    context_object_name = 'News'
    
    def get_queryset(self):
        return News.objects.order_by("-id")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context


class editNews(LoginRequiredMixin,UpdateView):
    model = News
    form_class = NewsForm
    template_name = 'Employee/General/News/updatenews.html'
    success_url = reverse_lazy('Employee_News_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'News Updated Successfully.')

        return super().form_valid(form)  
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
    
class OfferBannerCreateView(LoginRequiredMixin,CreateView):
    model = OfferBanner
    form_class = OfferBannerForm
    template_name = 'Employee/General/OfferBanner/addofferbanner.html'
    success_url = reverse_lazy('Employee_OfferBanner_list') 
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        
        messages.success(self.request, 'OfferBanner Added Successfully.')
          
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
class OfferBannerListView(LoginRequiredMixin,ListView):
    model = OfferBanner
    template_name = 'Employee/General/OfferBanner/offerbannerlist.html'  
    context_object_name = 'OfferBanner'
    
    def get_queryset(self):
        return OfferBanner.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context


class editOfferBanner(LoginRequiredMixin,UpdateView):
    model = OfferBanner
    form_class = OfferBannerForm
    template_name = 'Employee/General/OfferBanner/updateofferbanner.html'
    success_url = reverse_lazy('Employee_OfferBanner_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'OfferBanner Updated Successfully.')

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
    
class PackageCreateView(LoginRequiredMixin,CreateView):
    model = Package
    form_class = PackageForm
    template_name = 'Employee/Package/addpackage.html'
    success_url = reverse_lazy('Employee_Package_list')  
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['visa_countries'] = VisaCountry.objects.all()
        context['visa_categories'] = VisaCategory.objects.all()
        context['visa_subcategories'] = VisaSubcategory.objects.all()

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        
        # Handle the Word document file upload here
        word_doc = self.request.FILES.get('word_doc')
        if word_doc:
            # Save the Word document to the appropriate directory
            form.instance.word_doc = word_doc
        
        messages.success(self.request, 'Package Added Successfully.')
        return super().form_valid(form)
    
    
class PackageListView(LoginRequiredMixin,ListView):
    model = Package
    template_name = 'Employee/Package/packagelist.html'  
    context_object_name = 'Package'
    
    def get_queryset(self):
        return Package.objects.order_by("-id")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context


class editPackage(LoginRequiredMixin,UpdateView):
    model = Package
    form_class = PackageForm
    template_name = 'Employee/Package/packageupdate.html'
    success_url = reverse_lazy('Employee_Package_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'Package Updated Successfully.')

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
    
class FrontWebsiteEnquiryCreateView(LoginRequiredMixin,CreateView):
    model = FrontWebsiteEnquiry
    form_class = FrontWebsiteEnquiryForm
    template_name = 'Employee/FrontWebsiteEnquiry/addenquiry.html'
    success_url = reverse_lazy('Employee_FrontWebsiteEnquiry_list') 
    
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        user = self.request.user
        
        messages.success(self.request, 'FrontWebsiteEnquiry Added Successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
    
class FrontWebsiteEnquiryListView(LoginRequiredMixin,ListView):
    model = FrontWebsiteEnquiry
    template_name = 'Employee/FrontWebsiteEnquiry/FrontWebsiteEnquirylist.html'  
    context_object_name = 'FrontWebsiteEnquiry'
    
    def get_queryset(self):
        return FrontWebsiteEnquiry.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context

@login_required
def view_frontenqlist(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    
    enq = FrontWebsiteEnquiry.objects.get(id=id)
    context={
        "enq":enq,
        "assigned_menus":assigned_menus
    }
    return render(request,'Employee/FrontWebsiteEnquiry/viewfrontenquiry.html',context)      

def get_client_ip(request: HttpRequest) -> str:
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_public_ip():
        try:
            response = requests.get('https://api64.ipify.org?format=json')
            data = response.json()
            return data['ip']
        except Exception as e:
            # Handle the exception (e.g., log the error)
            return None


class enrolled_Application(LoginRequiredMixin,ListView):
    model = Enquiry
    template_name = 'Employee/ApplicationManagement/EnrolledApplication/enrolledapplicationlist.html'  
    context_object_name = 'enquiry'

    def get_queryset(self):
        user = self.request.user
        return Enquiry.objects.filter(
            Q(assign_to_employee=user.employee) &
            (
                Q(lead_status="Enrolled") |
                Q(lead_status="Inprocess") |
                Q(lead_status="Ready To Submit") |
                Q(lead_status="Appointment") |
                Q(lead_status="Ready To Collection") |
                Q(lead_status="Result") |
                Q(lead_status="Delivery") |
                Q(lead_status="Case Initiated")
            )
        ).order_by("-id")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        current_datetime = timezone.now()
        context['current_datetime'] = current_datetime

        context['notes'] = Notes.objects.all()
        context['notes_first'] = Notes.objects.order_by('-id').first()
        context['employee_queryset'] = Employee.objects.all()
        context['agents'] = Agent.objects.filter(registerdby=self.request.user)
        context['OutSourcingAgent'] = OutSourcingAgent.objects.filter(registerdby=self.request.user)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

        context['assigned_menus'] = assigned_menus

        return context
      
@login_required
def enrolled_add_notes(request):
    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        notes_text = request.POST.get('notes')
        file = request.FILES.get('file')
        user = request.user

        try:
            enq = Enquiry.objects.get(id=enq_id)
            ip_address = get_public_ip()
            
            # Get the client's IP address
            
            
            # Create the Notes instance with the Enquiry instance and IP address
            notes = Notes.objects.create(enquiry=enq, notes=notes_text, file=file, ip_address=ip_address, created_by=user)
            notes.save()
            
        except Enquiry.DoesNotExist:
            # Handle the case where the Enquiry with the given ID does not exist
            pass  # You can add appropriate error handling here if needed
    
    return redirect('Employee_enroll_application')

 
@login_required
def assign_agent(request):
    if request.method == "POST":
        
        enq_id = request.POST.get('enq_id')
        lead_status = request.POST.get('lead_status')
        agent_id = request.POST.get('agent_id')

        enq = Enquiry.objects.get(id=enq_id)

        agent = Agent.objects.get(id=agent_id)
        enq.assign_to_agent = agent
        enq.save()

    return redirect('Employee_enroll_application')



@login_required
def assign_outsourceagent(request):
    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        
        outsourceagent_id = request.POST.get('outsourceagent_id')

        enq = Enquiry.objects.get(id=enq_id)
        out_sourceagent = OutSourcingAgent.objects.get(id=outsourceagent_id)
        enq.assign_to_outsourcingagent = out_sourceagent
        enq.lead_status = "Case Initiated"
        enq.save()


    return redirect('Employee_enroll_application')


@login_required
def assign_employee(request):
    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        emp_id = request.POST.get('emp_id')

        enq = Enquiry.objects.get(id=enq_id)
        employee = Employee.objects.get(id=emp_id)
        enq.assign_to_employee = employee
        enq.save()


    return redirect('Employee_enroll_application')

@login_required
def edit_enrolled_application(request,id):


    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    enquiry = Enquiry.objects.get(id=id)
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()
    subcategory = VisaSubcategory.objects.all()
    context ={
        'enquiry':enquiry,
        'country':country,
        'category':category,
        'subcategory':subcategory,
        "assigned_menus":assigned_menus
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
        return redirect("Employee_edit_enrolled_application", id=id)

    return render(
        request,
        "Employee/ApplicationManagement/EnrolledApplication/editenrolledapplication.html",
        context,
    )
  

@login_required
def education_summary(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    
    enquiry = Enquiry.objects.get(id=id)
    # education_summary = Education_Summary.objects.get(enquiry_id=enquiry)
    if Education_Summary.objects.filter(enquiry_id=enquiry).exists():
        education_summary = Education_Summary.objects.get(enquiry_id=enquiry)
    else:
        # Handle the case where there is no matching Education_Summary
        education_summary = None 

    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        educationcountry = request.POST.get('educationcountry')
        highest_education = request.POST.get('highest_education')
        gradingscheme = request.POST.get('gradingscheme')
        gradeaverage = request.POST.get('gradeaverage')
        recent_college = request.POST.get('recent_college')
        level_education = request.POST.get('level_education')
        institutecountry = request.POST.get('institutecountry')
        institutename = request.POST.get('institutename')
        instructionlanguage = request.POST.get('instructionlanguage')
        institutionfrom = request.POST.get('institutionfrom')
        institutionto = request.POST.get('institutionto')
        degreeawarded = request.POST.get('degreeawarded')
        degreeawardedon = request.POST.get('degreeawardedon')
        address = request.POST.get('address')
        city = request.POST.get('city')
        province = request.POST.get('province')
        zipcode = request.POST.get('zipcode')

        # education_summary = Education_Summary.objects.get(enquiry_id=enq_id)
        # education_summary, created = Education_Summary.objects.get_or_create(enquiry_id=enq_id)
        enquiry = get_object_or_404(Enquiry, id=enq_id)
        education_summary, created = Education_Summary.objects.get_or_create(enquiry_id=enquiry)
        education_summary.country_of_education =educationcountry
        education_summary.highest_level_education =highest_education
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
        return redirect('Employee_education_summary',id=id)
        

        # education_summary = Education_Summary.objects.create(enquiry_id=enq_id,country_of_education=educationcountry,highest_level_education=highest_education,grading_scheme=gradingscheme,grade_avg=gradeaverage,recent_college=recent_college)
    context = {
        'enquiry':enquiry,
        'education_summary':education_summary,
        "assigned_menus":assigned_menus
    }
    return render(request,'Employee/ApplicationManagement/EnrolledApplication/Subforms/education-form.html',context)



@login_required
def test_score(request, id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    
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

        return redirect("Employee_test_score", id=id)

    context = {
        "test_score": test_score,
        "enquiry_id": enquiry_id,
        "assigned_menus":assigned_menus
    }
    return render(request, 'Employee/ApplicationManagement/EnrolledApplication/Subforms/test-score-form.html', context)




@login_required
def delete_test_score(request, id):
    test_score = TestScore.objects.get(id=id)
    enquiry_id = test_score.enquiry_id.id
    test_score.delete()
    return redirect("Employee_test_score", id=enquiry_id)
   
    
@login_required
def background_information(request, id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    enquiry_id = Enquiry.objects.get(id=id)
    
    try:
        # Try to retrieve an existing Background_Information entry for this enquiry

        bk_info = Background_Information.objects.get(enquiry_id=enquiry_id)

        if request.method == "POST":
            exaustralliabeforeamtype = request.POST.get("australliabefore")

            # Update the existing Background_Information entry
            bk_info.background_information = exaustralliabeforeamtype
            bk_info.save()

            return redirect("Employee_background_information", id=id)
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
            
            return redirect('Employee_background_information', id=id)
    
    context = {
        'bk_info': bk_info,
        'enquiry_id': enquiry_id,
        "assigned_menus":assigned_menus
    }
    return render(request, 'Employee/ApplicationManagement/EnrolledApplication/Subforms/background-form.html', context)


@login_required
def documents(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    enquiry_id = Enquiry.objects.get(id=id)
    documents = ApplicationDocuments.objects.filter(enquiry_id=enquiry_id)
    context = {
        "enquiry_id":enquiry_id,
        "documents":documents,
	"assigned_menus":assigned_menus
    }
    return render(request, 'Employee/ApplicationManagement/EnrolledApplication/Subforms/document-form.html', context)


@login_required
def create_documents(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    enquiry_id = Enquiry.objects.get(id=id)
    context = {
        "assigned_menus":assigned_menus
    }
    
    if request.method == "POST":
        documentname = request.POST.get('documentname')
        comment = request.POST.get('comment')
        files = request.FILES.get('files')
        documts = ApplicationDocuments.objects.create(enquiry_id=enquiry_id,document_name=documentname,comments=comment,upload_documents=files)
        documts.save()
    return redirect('Employee_documents', id=id, context=context)

@login_required
def timeline(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    enquiry_id = Enquiry.objects.get(id=id)
    context = {
        "enquiry_id":enquiry_id,
        "assigned_menus":assigned_menus
    }
    return render(request, 'Employee/ApplicationManagement/EnrolledApplication/Subforms/timeline-form.html', context)

@login_required
def workexperience(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
        
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

            return redirect("Employee_workexperience", id=id)
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

            return redirect("Employee_workexperience", id=id)

    
    context = {
        "enquiry_id": enquiry_id,
        "work_exp": work_exp,
        "assigned_menus":assigned_menus
    }
    return render(request, 'Employee/ApplicationManagement/EnrolledApplication/Subforms/workexperience-form.html', context)



# def upload_to(request):

@login_required   
def upload_to(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']

        # Save the file to a temporary location (you can customize this)
        fs = FileSystemStorage(location='media/temp/')
        filename = fs.save(uploaded_file.name, uploaded_file)

        # Now, you can save the file's data to your database model
        uploaded_data = UploadedFile(file=filename)  # Adjust this according to your model
        uploaded_data.save()

        # Optionally, you can delete the temporary file
        fs.delete(filename)

        return redirect('/')  # Redirect to a success page

    # return render(request, 'upload.html')
    return render(request,'Employee/ApplicationManagement/upload_to.html')



##################### Visa Case #####################


   
class ClientList(LoginRequiredMixin,ListView):
    model = Enquiry
    template_name = 'Employee/ApplicationManagement/VisaCases/visacaseslist.html'  
    context_object_name = 'enquiry'

    
    def get_queryset(self):
        
        queryset = Enquiry.objects.filter(lead_status="Case Initiated").order_by("-id")
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context


@login_required
def update_case_status(request,id):
    enq_id = Enquiry.objects.get(id=id)
    case_status = CaseStatus.objects.all()
    application_status = ApplicationStatus.objects.filter(enquiry_id=enq_id)
    
    if request.method == "POST":
        case_status_id = request.POST.get('case_status') 
        casestatus = CaseStatus.objects.get(id=case_status_id)
        enq_id.case_status=casestatus
        enq_id.save()
        appstatus = ApplicationStatus.objects.create(enquiry_id=enq_id,updated_by=request.user)

        appstatus.save()

    return render(request, 'Employee/ApplicationManagement/VisaCases/casestatus.html', {'enq_id': enq_id,'case_status':case_status,'application_status':application_status})

    # return redirect('Employee_update_case_status',id=id)

@login_required
def client_documents(request):
    return render(request,'Employee/ApplicationManagement/UserDocument/adduserdocument.html')


@login_required
def view_appointment(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    
    enq_id = Enquiry.objects.get(id=id)
    appointment = Appointment.objects.filter(enquiry_id=enq_id)
    context = {
        'enq_id':enq_id,
        'appointment':appointment,
        "assigned_menus":assigned_menus
    }
    return render(request,'Employee/ApplicationManagement/VisaCases/appointmentlist.html',context)

@login_required
def add_appointment(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    enquiry = Enquiry.objects.get(id=id)
    if request.method == "POST":
        title = request.POST.get('title')
        motive = request.POST.get('motive')
        date = request.POST.get('date')
        time = request.POST.get('time')
        is_paid = request.POST.get('is_paid') == 'on'
        print("is paid", is_paid)
        
        amount = request.POST.get('amount')
        paid_amt = request.POST.get('paid_amount')
        
        notes = request.POST.get('notes')

        try:
            appointment = Appointment.objects.create(
                enquiry_id=enquiry, title=title, motive=motive, date=date,
                time=time, is_paid=is_paid, amount=amount, paid_amt=paid_amt, notes=notes
            )
            appointment.save()
            print("hello ggg")
            
            return redirect('Employee_view_appointment',id=id)  # Modify 'appointment_detail' to your URL pattern name
        except Exception as e:
            
            pass  
    context = {
        'enquiry':enquiry,
        "assigned_menus":assigned_menus
    }


    return render(request,'Employee/ApplicationManagement/VisaCases/addappointment.html',context)


class loginlog(LoginRequiredMixin,ListView):
    model = LoginLog
    template_name = 'Employee/General/Loginlogs/loginlogs.html'
    context_object_name = 'loginlog'

    
    def get_queryset(self):
        # Filter LoginLog entries where user_type is not equal to '1'
        return LoginLog.objects.exclude(user__user_type='1').order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
  

@login_required
def search_loginlog(request):
    user = request.user
    if request.method == 'POST':
        
        
        # Check if the user_type is not '1' (HOD)
        if user.user_type != '1':
            from_date = request.POST.get('from_date')
            to_date = request.POST.get('to_date')
            email = request.POST.get('user_id')
            user_type = request.POST.get('user_type')
            print("emailll",email)
            # Start with the full queryset
            loginlog_queryset = LoginLog.objects.all()

            # Exclude records with user_type = '1' (HOD)
            loginlog_queryset = loginlog_queryset.exclude(user__user_type='1')

            # Apply filters based on user input
            if from_date:
                # Filter by date if from_date is provided
               from_date_datetime = datetime.strptime(from_date, '%Y-%m-%d')
            #Make from_date_datetime timezone-aware
               from_date_aware = timezone.make_aware(from_date_datetime, timezone.get_current_timezone())
            # Filter by date if from_date is provided
               loginlog_queryset = loginlog_queryset.filter(login_datetime__date=from_date_aware.date())
            if to_date:
                to_date_datetime = datetime.strptime(from_date, '%Y-%m-%d')
                to_date_aware = timezone.make_aware(to_date_datetime, timezone.get_current_timezone())
                # Filter by date if to_date is provided
                loginlog_queryset = loginlog_queryset.filter(login_datetime__date=to_date_aware.date())
            if email:
                # Filter by name if name is provided
                loginlog_queryset = loginlog_queryset.filter(user__email__exact=email)
            if user_type:
                # Filter by name if name is provided
                loginlog_queryset = loginlog_queryset.filter(user__user_type__icontains=user_type)

            return render(request, 'Employee/General/Loginlogs/loginlogs.html', {'loginlog': loginlog_queryset})

    # If the request method is not POST or user_type is '1' (HOD), display all records except user_type '1'
    loginlog_queryset = LoginLog.objects.exclude(user__user_type='1')

    return render(request, 'Employee/General/Loginlogs/loginlogs.html', {'loginlog': loginlog_queryset})  

 
@login_required
def add_agent(request):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    context = {
        
        "assigned_menus":assigned_menus
    }
    
    logged_in_user = CustomUser.objects.get(username=request.user.username)
    print(logged_in_user)
    if request.method == "POST":
        type = request.POST.get('type')
        # department = request.POST.get('department')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        password = request.POST.get('password')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        address = request.POST.get('address')
        zipcode = request.POST.get('zipcode')
        activeinactive = request.POST.get('status')
        files = request.FILES.get('files')
       
        
        existing_agent= CustomUser.objects.filter(username=email)
        try:
            if existing_agent:
                messages.warning(request, f'"{email}" already exists.')
                return redirect('add_agent')
            if type == "Outsourcing Partner":
                user = CustomUser.objects.create_user(username=email,first_name=firstname,last_name=lastname,email=email,password=password,user_type='5')
                logged_in_user = CustomUser.objects.get(username=request.user.username)
            
            
            # print("userssssssssss",users)
                user.outsourcingagent.type=type
                user.outsourcingagent.contact_no=contact
                user.outsourcingagent.country=country
                user.outsourcingagent.state=state
                user.outsourcingagent.City=city
                user.outsourcingagent.Address=address
                user.outsourcingagent.zipcode=zipcode
                user.outsourcingagent.activeinactive=activeinactive
                user.outsourcingagent.profile_pic=files
                user.outsourcingagent.registerdby = logged_in_user
                user.save()
            #     subject = 'Congratulations! Your Account is Created'
            #     message = f'Hello {firstname} {lastname},\n\n' \
            #         f'Welcome to SSDC \n\n' \
            #         f'Congratulations! Your account has been successfully created as an agent.\n\n' \
            #         f' Your id is {email} and your password is {password}.\n\n' \
            #         f' go to login : https://crm.theskytrails.com/Agent/Login/ \n\n' \
            #         f'Thank you for joining us!\n\n' \
            #         f'Best regards,\nThe Sky Trails'  # Customize this message as needed

            # # Change this to your email
            #     recipient_list = [email]  # List of recipient email addresses

            #     send_mail(subject, message, from_email=None, recipient_list=recipient_list)
                messages.success(request, 'OutSource Agent Added Successfully')
                return redirect('empall_outsource_agent')
                

            else:
                user = CustomUser.objects.create_user(username=email,first_name=firstname,last_name=lastname,email=email,password=password,user_type='4')

            # users = request.user.username
                logged_in_user = CustomUser.objects.get(username=request.user.username)
            
            
            # print("userssssssssss",users)
                user.agent.type=type
                user.agent.contact_no=contact
                user.agent.country=country
                user.agent.state=state
                user.agent.City=city
                user.agent.Address=address
                user.agent.zipcode=zipcode
                user.agent.activeinactive=activeinactive
                user.agent.profile_pic=files
                user.agent.registerdby = logged_in_user
                user.save()

            #     subject = 'Congratulations! Your Account is Created'
            #     message = f'Hello {firstname} {lastname},\n\n' \
            #         f'Welcome to SSDC \n\n' \
            #         f'Congratulations! Your account has been successfully created as an agent.\n\n' \
            #         f' Your id is {email} and your password is {password}.\n\n' \
            #         f' go to login : https://crm.theskytrails.com/Agent/Login/ \n\n' \
            #         f'Thank you for joining us!\n\n' \
            #         f'Best regards,\nThe Sky Trails'   # Customize this message as needed

            # # Change this to your email
            #     recipient_list = [email]  # List of recipient email addresses

            #     send_mail(subject, message, from_email=None, recipient_list=recipient_list)

                messages.success(request, 'Agent Added Successfully')
                return redirect('Employee_all_agent')
        except Exception as e:
            messages.warning(request,e)
    return render(request,'Employee/agentmanagement/addagent.html',context)


class all_agent(LoginRequiredMixin,ListView):
    model = Agent
    template_name = 'Employee/agentmanagement/agentlist.html'  
    context_object_name = 'agent'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus
            

        return context

    def get_queryset(self):
        user = self.request.user
        current_employee = user.employee
        return Agent.objects.filter(
            Q(registerdby=user) | Q(assign_employee=current_employee)
        ).order_by("-id")



class all_outsource_agent(LoginRequiredMixin,ListView):
    model = OutSourcingAgent
    template_name = 'Employee/agentmanagement/agentoutsourcelist.html'  
    context_object_name = 'agentoutsource'
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context

    def get_queryset(self):
        user = self.request.user
        current_employee = user.employee
        return OutSourcingAgent.objects.filter(
            Q(registerdby=user) | Q(assign_employee=current_employee)
        ).order_by("-id")
        
        
        
@login_required
def outsourceagent_agreement(request, id):


    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    
    outsource = OutSourcingAgent.objects.get(id=id)
    
    agrmnt = AgentAgreement.objects.filter(outsourceagent=outsource)
    context = {
        
        'outsource':outsource,
        'agrmnt':agrmnt,
	"assigned_menus":assigned_menus
    }

    if request.method == "POST":

        
        outsource_id = request.POST.get('outsource_id')
        agreementname = request.POST.get('agreementname')
        agreement_file = request.FILES.get('agreement_file')

       
        
        outsource = OutSourcingAgent.objects.get(id=outsource_id)
        agreement = AgentAgreement.objects.create(outsourceagent=outsource, agreement_name=agreementname, agreement_file=agreement_file)
        agreement.save()
        print("Outsource agreement saved successfully")
        
        return redirect('empoutsourceagent_agreement',id=id)

    return render(request,'Employee/agentmanagement/outsourceagreement-form.html',context)

@login_required
def outsource_kyc(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())    

    outsource = OutSourcingAgent.objects.get(id=id)
    kyc = AgentAgreement.objects.filter(outsourceagent=outsource)
    
    context = {
        'outsource':outsource,
        'kyc':kyc,
        "assigned_menus":assigned_menus
    }
    
    if request.method == "POST":
        adharfront_file = request.FILES.get('adharfront_file')
        adharback_file = request.FILES.get('adharback_file')
        pan_file = request.FILES.get('pan_file')
        registration_file = request.FILES.get('registration_file')
        if adharfront_file:
            print("ssssssssss",adharfront_file)
            outsource.adhar_card_front = adharfront_file
            outsource.save()
        elif adharback_file:
            print("dddddddddd",adharback_file)
            outsource.adhar_card_back = adharback_file
            outsource.save()
        elif pan_file:
            print("dddddddddd",pan_file)
            outsource.pancard = pan_file
            outsource.save()
        elif registration_file:
            print("dddddddddd",registration_file)
            outsource.registration_certificate = registration_file
            outsource.save()

    return render(request,'Employee/agentmanagement/agentoutsourcekyc-form.html',context)

@login_required
def agent_update(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    
    agent = get_object_or_404(Agent, id=id)

    if request.method == "POST":
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        maritial = request.POST.get('maritial')
        original_pic = request.FILES.get('original_pic')
        organization = request.POST.get('organization')
        business_type = request.POST.get('business_type')
        registration = request.POST.get('registration')
        address = request.POST.get('registration')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zipcode = request.POST.get('zipcode')
        accountholder = request.POST.get('accountholder')
        bankname = request.POST.get('bankname')
        branchname = request.POST.get('branchname')
        account = request.POST.get('account')
        ifsc = request.POST.get('ifsc')

        if dob:
            agent.dob = dob
        if gender:
            agent.gender = gender
        if maritial:
            agent.marital_status = maritial
        agent.profile_pic = original_pic
        agent.organization_name = organization
        agent.business_type = business_type
        agent.registration_number = registration
        agent.Address = address
        agent.country = country
        agent.state = state
        agent.City = city
        agent.zipcode = zipcode
        agent.account_holder = accountholder
        agent.bank_name = bankname
        agent.branch_name = branchname
        agent.account_no = account
        agent.ifsc_code = ifsc
        agent.save()
        messages.success(request,'Updated Successfully')
        return redirect('Employee_all_agent')

    context = {
        'agent':agent,
        "assigned_menus":assigned_menus
        
    }
    return render(request,'Employee/agentmanagement/agentupdate.html',context)


@login_required
def outsourceagent_update(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())
    
    agent = OutSourcingAgent.objects.get(id=id)

    if request.method == "POST":
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        maritial = request.POST.get('maritial')
        original_pic = request.FILES.get('original_pic')
        organization = request.POST.get('organization')
        business_type = request.POST.get('business_type')
        registration = request.POST.get('registration')
        address = request.POST.get('registration')
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        zipcode = request.POST.get('zipcode')
        accountholder = request.POST.get('accountholder')
        bankname = request.POST.get('bankname')
        branchname = request.POST.get('branchname')
        account = request.POST.get('account')
        ifsc = request.POST.get('ifsc')

        if dob:
            agent.dob = dob
        if gender:
            agent.gender = gender
        if maritial:
            agent.marital_status = maritial
        agent.profile_pic = original_pic
        agent.organization_name = organization
        agent.business_type = business_type
        agent.registration_number = registration
        agent.Address = address
        agent.country = country
        agent.state = state
        agent.City = city
        agent.zipcode = zipcode
        agent.account_holder = accountholder
        agent.bank_name = bankname
        agent.branch_name = branchname
        agent.account_no = account
        agent.ifsc_code = ifsc
        agent.save()
        messages.success(request,'Updated Successfully')
        return redirect('empall_outsource_agent')

    context = {
        
        'agent':agent,
        "assigned_menus":assigned_menus
    }
    return render(request,'Employee/agentmanagement/outsourceagentupdate.html',context)

@login_required
def agent_agreement(request, id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    try:
        agent = Agent.objects.get(id=id)
        outsource = OutSourcingAgent.objects.get(id=id)
    except Agent.DoesNotExist:
        agent = None
    except OutSourcingAgent.DoesNotExist:
        outsource = None

    agrmnt = AgentAgreement.objects.filter(agent=agent)
    context = {
        'agent':agent,
        'outsource':outsource,
        'agrmnt':agrmnt,
        "assigned_menus":assigned_menus
    }

    if request.method == "POST":

        agent_id = request.POST.get('agent_id')
        outsource_id = request.POST.get('outsource_id')
        agreementname = request.POST.get('agreementname')
        agreement_file = request.FILES.get('agreement_file')

        if agent_id:
            agent = Agent.objects.get(id=agent_id)
            agreement = AgentAgreement.objects.create(agent=agent,agreement_name=agreementname,agreement_file=agreement_file)
            agreement.save()
            print("Agent agreement saved successfully")
        elif outsource_id:
            outsource = OutSourcingAgent.objects.get(id=outsource_id)
            agreement = AgentAgreement.objects.create(outsourceagent=outsource, agreement_name=agreementname, agreement_file=agreement_file)
            agreement.save()
            print("Outsource agreement saved successfully")
        else:
            print("Neither agent_id nor outsource_id found in the POST data")
        return redirect('empagent_agreement',id=id)

    return render(request,'Employee/agentmanagement/agreement-form.html',context)

@login_required
def agent_kyc(request,id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    agent = Agent.objects.get(id=id)
    context = {
        'agent':agent,
        "assigned_menus":assigned_menus
    }
    
    if request.method == "POST":
        adharfront_file = request.FILES.get('adharfront_file')
        adharback_file = request.FILES.get('adharback_file')
        pan_file = request.FILES.get('pan_file')
        registration_file = request.FILES.get('registration_file')
        if adharfront_file:
            print("ssssssssss",adharfront_file)
            agent.adhar_card_front = adharfront_file
            agent.save()
        elif adharback_file:
            print("dddddddddd",adharback_file)
            agent.adhar_card_back = adharback_file
            agent.save()
        elif pan_file:
            print("dddddddddd",pan_file)
            agent.pancard = pan_file
            agent.save()
        elif registration_file:
            print("dddddddddd",registration_file)
            agent.registration_certificate = registration_file
            agent.save()

    return render(request,'Employee/agentmanagement/kyc-form.html',context)

@login_required
def agent_status_update(request):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    context = {
        "assigned_menus":assigned_menus
    }
    
    if request.method == "POST":
        agent_id = request.POST.get('agent_id')
        
        status = request.POST.get('status')
        print("status",status)
        try:
            agent = Agent.objects.get(id=agent_id)
            agent.status = status
            agent.save()
            
        except Agent.DoesNotExist:
            # Handle the case where the agent doesn't exist
            return redirect('Employee_all_agent')  # Redirect to some appropriate URL
        # agent.status = status
        # return redirect('all_agent')

        url = reverse('Employee_all_agent')
    return redirect(url, assigned_menus=context)


class DepartmentCreateView(LoginRequiredMixin,CreateView):

    model = Department
    form_class = DepartmentForm
    template_name = 'Employee/Rolesmanagement/addrole.html'
    success_url = reverse_lazy('Employee_Department_list') 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
    
class DepartmentListView(LoginRequiredMixin,ListView):
    model = Department
    template_name = 'Employee/Rolesmanagement/rolelist.html'  
    context_object_name = 'role'
    
    def get_queryset(self):
        return Department.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
class editDepartment(LoginRequiredMixin,UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'Employee/Rolesmanagement/roleupdate.html'
    success_url = reverse_lazy('Employee_Department_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'Department Updated Successfully.')

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
     

@login_required(login_url='/') 
def ChangePassword(request):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    context = {
        "assigned_menus":assigned_menus
    }

    user = request.user
    employee = Employee.objects.get(users=user)
    
    if request.method == "POST":
        old_psw = request.POST.get('old_password')
        newpassword = request.POST.get('newpassword')
        confirmpassword = request.POST.get('confirmpassword')
        
        if check_password(old_psw, employee.users.password):
            if newpassword == confirmpassword:
                # Set the new password for the user
                employee.users.set_password(newpassword)
                employee.users.save()
                messages.success(request,"Password changed successfully Please Login Again !!")
                return HttpResponseRedirect(reverse("ChangePassword"))
            else:
                messages.success(request,"New passwords do not match")
                return HttpResponseRedirect(reverse("ChangePassword"))
                
        else:
            # print("Old password is not correct")
            messages.warning(request,'Old password is not correct')
            
       
    return render(request, 'Employee/ChangePassword/changepassword.html',context)


class all_appointment(LoginRequiredMixin,ListView):
    model = Appointment
    template_name = 'Employee/Appointment/appointmentlist.html'
    context_object_name = 'appointment'
    
    def get_queryset(self):
        return Appointment.objects.order_by("-id")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context

@login_required
def AssignRoleView(request):
    if request.method == "POST":
        department_id = request.POST.get('department')
        menu_choice = request.POST.getlist('menu_choice')
        employee_ids = request.POST.getlist('employee')
        print("Ssssssssssssssss",employee_ids)

        try:
            department = Department.objects.get(id=department_id)
            menu_id = Menu.objects.filter(id__in=menu_choice)
            print("hellooo")
            employees = Employee.objects.filter(id__in=employee_ids)
            
           

            role_assignment = AssignRoles.objects.create(department=department)

            role_assignment.menu_name.set(menu_id)
            
            #Add employees to the role_assignment one by one
            for employee in employees:
                messages.success(request, 'Role assigned successfully.')
                print("emplaaaa",employee)
                role_assignment.employee.add(employee)

            print("success")
            return redirect('Employee_assign_permissions')  # Replace 'success_url' with the appropriate URL

        except Exception as e:
            print("Error:", str(e))
        
        

    # Fetch departments and employees for rendering the form
    departments = Department.objects.all()
    employees = Employee.objects.all()
    menu_choices = Menu.objects.all()

    context = {
        "department": departments,
        "employee": employees,
        "menu_choices": menu_choices,
    }

    return render(request, 'Employee/permission.html', context)


def fetch_users(request):
    
    category_id = request.GET.get('category_id')
    subcategories = Employee.objects.filter(department=category_id)
    # data = list(subcategories.values('id', 'users'))
    data = [{'id': emp.id, 'first_name': emp.users.first_name,'last_name': emp.users.last_name,'department': emp.department.name} for emp in subcategories]
    return JsonResponse(data, safe=False)
    print("category_id",category_id)

def get_users_for_department(request):
    department_id = request.GET.get('department_id')
    if department_id:
        users = CustomUser.objects.filter(employee__department=department_id)
        user_list = [{'id': user.id, 'username': user.username} for user in users]
        return JsonResponse(user_list, safe=False)
    else:
        return JsonResponse([], safe=False)

def handle_permissions(request):
    if request.method == 'POST':
        # Get the selected department, menu choices, and users from the form data
        department_id = request.POST.get('department')
        selected_menu_choices = request.POST.getlist('menu_name')
        selected_users = request.POST.getlist('users')

        try:
            department = Department.objects.get(id=department_id)
        except Department.DoesNotExist:
            return HttpResponse("Invalid department")

        # Clear existing permissions for the selected department
        AssignRoles.objects.filter(department=department).delete()

        # Assign new permissions based on selected menu choices and users
        for menu_choice in selected_menu_choices:
            # Here, menu_choice will be one of the choices defined in your model
            for user_id in selected_users:
                try:
                    user = CustomUser.objects.get(id=user_id)
                except CustomUser.DoesNotExist:
                    return HttpResponse(f"Invalid user ID: {user_id}")

                # Create a new AssignRoles entry for each combination
                AssignRoles.objects.create(department=department, menu_name=menu_choice, users=user)

        return HttpResponse("Permissions assigned successfully")

    # Handle GET requests or other cases
    # You can render a template or return an appropriate response
    return HttpResponse("Invalid request")

@login_required
def AssignRolelist(request):
    assign_roles = AssignRoles.objects.all().order_by("-id")

    context = {
        'assign_roles': assign_roles,
    }

    return render(request, 'Employee/Rolesmanagement/assign_roles_list.html', context)


class FAQCreateView(LoginRequiredMixin,CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'Employee/FAQ/addfaq.html'
    success_url = reverse_lazy('Employee_faqlist') 
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        messages.success(self.request, 'FAQ Added Successfully.')
          
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
    
class FAQListView(LoginRequiredMixin,ListView):
    model = FAQ
    template_name = 'Employee/FAQ/faqlist.html'
    context_object_name = 'FAQs'
    
    def get_queryset(self):
        return FAQ.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context

class FAQUpdateView(LoginRequiredMixin,UpdateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'Employee/FAQ/updatefaq.html'  
    success_url = reverse_lazy('Employee_faqlist')

    def form_valid(self, form):

        # Display a success message
        messages.success(self.request, 'FAQ updated successfully.')

        return super().form_valid(form)
   
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context

@login_required    
def delete_faq(request, id):

    assign_roles = AssignRoles.objects.filter(employee=request.user.employee)
    

    user = request.user
    assigned_menus = Menu.objects.filter(assignroles__employee=user.employee)
    


    assigned_menus = []
    for role in assign_roles:
        assigned_menus.extend(role.menu_name.all())

    context = {
        "assigned_menus":assigned_menus
    }
    
    faq = get_object_or_404(FAQ, id=id)
    faq.delete()
    url = reverse('Employee_faqlist')
    return redirect(url, assigned_menus=context)


class enquiryfollowupList(LoginRequiredMixin,ListView):
    model = FollowUp
    template_name = "Employee/followups/enquiryfollowups.html"
    context_object_name = 'enquiryfollowup'
    
    def get_queryset(self):
        # Get the currently logged-in user
        user = self.request.user
        
        # Filter FollowUp objects by related Enquiry instances where assign_to_employee matches the user's employee
        queryset = FollowUp.objects.filter(enquiry__assign_to_employee=user.employee).order_by("-id")
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        return context
        
        
class EnrolledApplicationView(LoginRequiredMixin , DetailView):
    model = Enquiry
    template_name = "Employee/ApplicationManagement/EnrolledApplication/viewenrolledapplication.html"
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


def get_country_data(request):
    user = request.user

    country_data = (
        Enquiry.objects.filter(assign_to_employee=user.employee)
        .values("Visa_country__country")
        .annotate(total_inquiries=Count("id"))
    )
    print("country datasssssssss..........................", country_data)

    # Convert the queryset to a list of dictionaries
    country_data_list = list(country_data)

    return JsonResponse(country_data_list, safe=False)


def leads_detail(request, country_name):
    users = request.user
    assigned_menus = []

    if users.is_authenticated:
        assign_roles = AssignRoles.objects.filter(employee=users.employee)

        for role in assign_roles:
            assigned_menus.extend(role.menu_name.all())

    enquiry = Enquiry.objects.filter(
        assign_to_employee=users.employee, Visa_country__country=country_name
    )
    print("Employeee Dashboard", enquiry)
    # Get the country code from the URL parameter
    # country_code = request.GET.get("country")
    # country_name = request.GET.get("country_name")

    # You can add logic here to retrieve and display the leads for the selected country
    # For example, you can query your database to get leads related to the selected country

    # Replace this with your actual logic for displaying leads data
    # For now, it just displays the selected country code as an example
    # return HttpResponse(f"Leads for Country: {country_name}")
    context = {"enq": enquiry, "assigned_menus": assigned_menus}
    return render(request, "Employee/CountryWiseLeads/enquiry_list.html", context)
    
    
@login_required
def Agent_leads(request):
    users = request.user
    assigned_menus = []

    if users.is_authenticated:
        assign_roles = AssignRoles.objects.filter(employee=users.employee)

        for role in assign_roles:
            assigned_menus.extend(role.menu_name.all())
    agent = Agent.objects.filter(assign_employee=users.employee)
    statuses_to_include = ['Inprocess', 'Ready To Submit', 'Appointment','Ready To Collection','Result' ,'Delivery']
    enquiries = Enquiry.objects.filter(assign_to_agent__in=agent,lead_status__in=statuses_to_include)
        

    context = {
        'enquiries': enquiries,
        'assigned_menus':assigned_menus
    }

    return render(request, 'Employee/Leads/agentleads.html', context)

from django.core.cache import cache
@login_required
def agent_emp_lead_enquiry(request):
    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        lead_status = request.POST.get('lead_status')

        
        enq = Enquiry.objects.get(id=enq_id)
        
        firstname = enq.FirstName
        lastname=enq.LastName
        mob =enq.contact
        enq_number = enq.enquiry_number
        if lastname:
            full_name = firstname + " " + lastname
        else:
            full_name = firstname 
        
        if enq.lead_status == "Case Initiated":
            messages.warning(request,'Enquiry Status Not Updated As Visa Case Is Already Inititated.')
            return redirect('agentall_leads')
        enq.lead_status=lead_status
        
        if enq.lead_status == "Ready To Submit":
            # Get the last assigned employee index from the cache
            last_assigned_index = cache.get('last_assigned_index') or 0

            # Get the next employee in a round-robin manner
            visa_team_employees = get_visa_team_employee()
            if visa_team_employees.exists():
                next_index = (last_assigned_index + 1) % visa_team_employees.count()
                enq.assign_to_employee = visa_team_employees[next_index]
                enq.save()

                # Update the last assigned index in the cache
                cache.set('last_assigned_index', next_index)
                
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


    return redirect('agentall_leads')

def get_visa_team_employee():
    return Employee.objects.filter(department__name='Visa Team')

@login_required
def add_notes(request):
    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        notes_text = request.POST.get('notes')
        file = request.FILES.get('file')
        user = request.user

        try:
            enq = Enquiry.objects.get(id=enq_id)
            ip_address = get_public_ip()
            
            # Get the client's IP address
            
            
            # Create the Notes instance with the Enquiry instance and IP address
            notes = Notes.objects.create(enquiry=enq, notes=notes_text, file=file, ip_address=ip_address, created_by=user)
            notes.save()
            
        except Enquiry.DoesNotExist:
            # Handle the case where the Enquiry with the given ID does not exist
            pass  # You can add appropriate error handling here if needed
    
    return redirect('agentall_leads')
    
    
    
class profileview(TemplateView,LoginRequiredMixin):
    template_name = "Employee/profile.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = Enquiry.objects.filter(created_by=self.request.user)
        # employee = Employee.objects.all()
        agent = Agent.objects.filter(registerdby=self.request.user)
        
        user = self.request.user
        assigned_menus = []

        if user.is_authenticated:
            assign_roles = AssignRoles.objects.filter(employee=user.employee)

            for role in assign_roles:
                assigned_menus.extend(role.menu_name.all())

            context['assigned_menus'] = assigned_menus

        context['first_name'] = user.first_name
        context['last_name'] = user.last_name
        context['email'] = user.email
        context['contact'] = user.employee.contact_no
        # context['image'] = user.employee.file
        # print("uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",user.employee.file)
        context['department'] = user.employee.department
        if hasattr(user, 'get_user_type_display'):
            context['user_type'] = user.get_user_type_display()
        context['leads'] = leads
        context['agent'] = agent

        return context
    
    
@login_required
def edit_profile(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')

        employee_instance = Employee.objects.get(users=request.user)
        
        employee_instance.users.first_name = first_name
        employee_instance.users.last_name = last_name
        employee_instance.users.email = email
        employee_instance.contact_no = contact

        
        employee_instance.users.save()
        employee_instance.save()

        
        return redirect("Employee_profile")
        

    return render(request, 'Employee/profile.html')
    
