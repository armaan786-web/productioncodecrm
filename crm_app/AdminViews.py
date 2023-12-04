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
from django.core.mail import send_mail
from django.db.models import Count
from datetime import datetime, timedelta
from django.db.models.functions import TruncMonth

@login_required
def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")
    

class TravelDashboard(TemplateView):
    template_name = "dashboard/index2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Count the total number of agents
        agent_count = Agent.objects.count()

        # Count the total number of outsource agents
        outsourceagent_count = OutSourcingAgent.objects.count()

        # Count the total number of employees
        employee_count = Employee.objects.count()
        user = CustomUser.objects.all()
        # current_user = self.request.user
        logged_in_users = CustomUser.objects.filter(is_logged_in="True")

        # is_logged_in = LoginLog.objects.filter(user=current_user, logout_datetime=None).exists()

        # Count the total number of employees
        leadtotal_count = Enquiry.objects.all().count()
        leadaccept_count = Enquiry.objects.filter(lead_status="Accept").count()
        leadreject_count = Enquiry.objects.filter(lead_status="Reject").count()
        leadcaseinitiated_count = Enquiry.objects.filter(
            lead_status="Case Initiated"
        ).count()
        enquiry = Enquiry.objects.exclude(lead_status="New Lead").order_by(
            "-last_updated_on"
        )[:10]
        new_lead = Enquiry.objects.filter(lead_status="New Lead").order_by(
            "-last_updated_on"
        )[:10]
        package = Package.objects.all().order_by("-last_updated_on")[:10]

        enquiry_data = Enquiry.objects.values("Visa_country__country").annotate(
            count=Count("id")
        )

        labels = [item["Visa_country__country"] for item in enquiry_data]
        data = [item["count"] for item in enquiry_data]

        import calendar

        monthly_data = Enquiry.get_monthly_report()
        full_month_names = [calendar.month_name[item["month"]] for item in monthly_data]
        monthly_labels = [
            f"{item['year']}-{full_month_names[i]}"
            for i, item in enumerate(monthly_data)
        ]
        user_emp = Enquiry.objects.all()
        monthly_counts = (
            user_emp.annotate(month=TruncMonth("registered_on"))
            .values("month")
            .annotate(count=Count("id"))
        )
        labels = [entry["month"].strftime("%B %Y") for entry in monthly_counts]
        data = [entry["count"] for entry in monthly_counts]

        print("labelssss", labels)

        # monthly_labels = [f"{item['year']}-{item['month']:02}" for item in monthly_data]

        monthly_count = [item["enquiry_count"] for item in monthly_data]

        now = datetime.now()
        follow_ups_today = FollowUp.objects.filter(
            calendar=now.date(),
            time__lte=(now + timedelta(minutes=5)).time(),  # Adjust as needed
        )

        context["agent_count"] = agent_count
        context["employee_count"] = employee_count
        context["outsourceagent_count"] = outsourceagent_count
        context["leadpending_count"] = leadtotal_count
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

        context["monthly_labels"] = monthly_labels
        context["monthly_count"] = monthly_count
        context["follow_ups_today"] = follow_ups_today
        context["labels"] = labels
        context["data"] = data
        return context

    def get_month_name(self, month):
        return datetime(2023, month, 1).strftime("%b")


        
@login_required
def add_country(request):
    if request.method == "POST":
        print("heloooo")
        country = request.POST.get('countryname')
        status = request.POST.get('status')
        
        # try:
        user = request.user
        

        existing_country = VisaCountry.objects.filter(country=country)
        if existing_country:
            messages.warning(request, f'Country "{country}" already exists.')
            return redirect('add_country')
        
        visacountry = VisaCountry.objects.create(country=country,lastupdated_by=f"{user.first_name} {user.last_name}")
        if status:
            visacountry.status=status
        visacountry.save()
        messages.success(request,'Country Added Successfully !!')
        return redirect('visa_countrylist')
        # except Exception as e:
        #     messages.error(request,e)
            

    return render(request,'Admin/mastermodule/Visa/VisaCountry/addvisacountry.html')

@login_required
def visa_countrylist(request):
    country = VisaCountry.objects.all().order_by("-id")
    context = {
        'country':country
    }
    return render(request,'Admin/mastermodule/Visa/VisaCountry/visacountrylist.html',context)

# def visa_countryedit(request,id):
#     country_id = VisaCountry.objects.get(id=id)
@login_required
def visa_countryedit(request, id):
    # Retrieve the existing VisaCountry object
    country = get_object_or_404(VisaCountry, id=id)

    if request.method == "POST":
        # Handle form submission
        form = VisaCountryForm(request.POST, instance=country)  # Pass the instance to edit
        if form.is_valid():
            form.save()  # Save the updated data
            messages.success(request,'Country updated successfully.')
            return redirect('visa_countrylist')
    else:
        # Display the edit form with existing data
        form = VisaCountryForm(instance=country)

    return render(request, 'Admin/mastermodule/Visa/VisaCountry/visacountryupdate.html', {'form': form})


@login_required
def add_category(request):
    country = VisaCountry.objects.all()
    if request.method == "POST":
        country = request.POST.get('country_id')
        categoryname = request.POST.get('categoryname')
        status = request.POST.get('status')
        subcategory = request.POST.get('subcategory')
        try:
            
                
            user = request.user
            country_id = VisaCountry.objects.get(id=country)
            category = VisaCategory.objects.create(visa_country_id=country_id,category=categoryname,subcategory=subcategory,lastupdated_by=f"{user.first_name} {user.last_name}")
            if status:
                category.status = status

            category.save()
            messages.success(request,'Category Added Successfully !!')
            return redirect('category_list')
        except Exception as e:
            messages.error(request,'Something is Wrong Try Again !!')

        
    context = {
        'country':country
    }
    return render(request,'Admin/mastermodule/Visa/Category/addvisacategory.html',context)    

@login_required
def category_list(request):
    category = VisaCategory.objects.all().order_by("-id")
    context = {
        'category':category
    }
    return render(request,'Admin/mastermodule/Visa/Category/visacategorylist.html',context)    

 

@login_required
def visa_category_edit(request, id):
    # Retrieve the existing VisaCountry object
    category = get_object_or_404(VisaCategory, id=id)

    if request.method == "POST":
        # Handle form submission
        form = VisaCategoryForm(request.POST, instance=category)  # Pass the instance to edit
        if form.is_valid():
            form.save()  # Save the updated data
            messages.success(request, 'Category updated successfully.')
            return redirect('category_list')
    else:
        # Display the edit form with existing data
        form = VisaCategoryForm(instance=category)

    return render(request, 'Admin/mastermodule/Visa/Category/visacategoryupdate.html', {'form': form})

@login_required
def subcategory_list(request):
    subcategory = VisaSubcategory.objects.all().order_by("-id")
    context = {
        'subcategory':subcategory
    }
    return render(request,'Admin/mastermodule/Visa/VisaSubcategory/visasubcategorylist.html',context)


@login_required
def add_subcategory(request):
    country = VisaCountry.objects.all()
    category = VisaCategory.objects.all()
    person = CustomUser.objects.filter(user_type=3)

    context = {
        'country': country,
        'category': category,
        'person':person
    }

    if request.method == "POST":
        country_id = request.POST.get('country')
        category_id = request.POST.get('category')
        subcategory_name = request.POST.get('subcategory')
        amount = float(request.POST.get('amount') or 0)
        cgst = float(request.POST.get('cgst') or 0)
        sgst = float(request.POST.get('sgst') or 0)
        status = bool(request.POST.get('status'))
        user_id = request.POST.getlist('person')
        user = request.user

        # try:
            # Calculate the totalAmount
        total = amount+((amount * (cgst + sgst)) / 100)

        
        pricing = VisaSubcategory.objects.create(
            country_id_id=country_id,
            category_id_id=category_id,
            subcategory_name_id=subcategory_name,
            estimate_amt=amount,
            cgst=cgst,
            sgst=sgst,
            totalAmount=total,
            status=status,
            lastupdated_by=user.first_name,
            
        )
        pricing.person.set(user_id)
        pricing.save()

        messages.success(request, 'Subcategory Added Successfully !!')
        return redirect('subcategory_list')
        # except Exception as e:
        #     # Handle any exceptions here and possibly log them
        #     # messages.error(request, str(e))
        #     print("eeee",e)

    return render(request, 'Admin/mastermodule/Visa/VisaSubcategory/addvisasubcategory.html', context)

@login_required
def visa_subcategory_edit(request, id):
    instance = VisaSubcategory.objects.get(id=id)

    if request.method == "POST":
        form = VisasubCategoryForm(request.POST, instance=instance)
        if form.is_valid():
            user = request.user
            form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
            # Recalculate and update the totalAmount
            form.instance.totalAmount = form.instance.estimate_amt + ((form.instance.estimate_amt * (form.instance.cgst + form.instance.sgst)) / 100)
            form.save()  # Save the updated data, including the calculated totalAmount
            messages.success(request, 'Subcategory updated successfully.')
            return redirect('subcategory_list')
    else:
        form = VisasubCategoryForm(instance=instance)


    return render(request, 'Admin/mastermodule/Visa/VisaSubcategory/visasubcategoryupdate.html', {'form': form})


class DocumentCreateView(LoginRequiredMixin,CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'Admin/mastermodule/Manage Document/adddocument.html'
    success_url = reverse_lazy('document_list')  
    
    
    def form_valid(self, form):
        form.instance.lastupdated_by = self.request.user  
        messages.success(self.request, 'Document added successfully.')
        return super().form_valid(form)
 

   
class DocumentListView(LoginRequiredMixin,ListView):
    model = Document
    template_name = 'Admin/mastermodule/Manage Document/documentlist.html'
    context_object_name = 'documents'
    
    def get_queryset(self):
        return Document.objects.order_by("-id")

class DocumentUpdateView(LoginRequiredMixin,UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'Admin/mastermodule/Manage Document/documentupdate.html'  
    success_url = reverse_lazy('document_list')

    def form_valid(self, form):
        form.instance.lastupdated_by = self.request.user  

        # Display a success message
        messages.success(self.request, 'Document updated successfully.')

        return super().form_valid(form)

 
class MenuListView(LoginRequiredMixin,ListView):
    model = Menu
    template_name = 'Admin/Rolesmanagement/menulist.html'
    context_object_name = 'menu'
    
    def get_queryset(self):
        return Menu.objects.order_by("-id")



class AddMenu(LoginRequiredMixin,CreateView):
    model = Menu
    form_class = MenuForm
    template_name = 'Admin/Rolesmanagement/addmenu.html'
    success_url = reverse_lazy('Menu_list')  
    
    def form_valid(self, form):
        # Check if a menu item with the same name already exists
        name = form.cleaned_data['name']
        if Menu.objects.filter(name=name).exists():
            # Handle the case where the menu item already exists
            # You can add your custom logic here, such as showing an error message
            # or redirecting to a different page
            messages.warning(self.request, 'Menu item with this name already exists.')
            return redirect('add_menu')

        # If the menu item doesn't exist, proceed with saving it
        messages.success(self.request, 'Menu item has been successfully created.')
        return super().form_valid(form)


class EditMenuView(LoginRequiredMixin, UpdateView):
    model = Menu
    form_class = MenuForm
    template_name = 'Admin/Rolesmanagement/menuupdate.html'
    success_url = reverse_lazy('Menu_list')

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
           

class addcourieraddress(LoginRequiredMixin,View):
    def get(self,request):
        form = courieraddressForm()
        return render(request,'Admin/mastermodule/CourierAddress/addcourieraddress.html',{'form':form},)
    def post(self,request):
        form = courieraddressForm(request.POST)
        if form.is_valid():
            user = request.user
            form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
            form.save()
            messages.success(request, 'Courier Address Added successfully.')
            return redirect('viewcourieraddress_list')
        
@login_required
def viewcourieraddress_list(request):
    courier_addss = CourierAddress.objects.all().order_by("-id")
    context = {
        'courier_addss':courier_addss
    }
    return render(request,'Admin/mastermodule/CourierAddress/courieraddresslist.html',context)

@login_required
def courieraddressEdit(request, id):
    
    instance = CourierAddress.objects.get(id=id)

    if request.method == "POST":
        # Handle form submission
        form = courieraddressForm(request.POST, instance=instance)
        if form.is_valid():
            user = request.user
            form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
            form.save()  # Save the updated data
            messages.success(request, 'Courier Address updated successfully.')
            return redirect('viewcourieraddress_list')
    else:
        # Display the edit form with existing data
        form = courieraddressForm(instance=instance)

    return render(request,'Admin/mastermodule/CourierAddress/courieraddressupdate.html',{'form':form},)



class addcasestatus(LoginRequiredMixin,View):
    def get(self,request):
        form = CaseStatusForm()
        return render(request,'Admin/mastermodule/Case/addcasestatus.html',{'form':form},)
    def post(self,request):
        form = CaseStatusForm(request.POST)
        if form.is_valid():
            user = request.user
            form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
            form.save()
            messages.success(request, 'Case Status Added successfully.')
            return redirect('casestatuslist')

@login_required
def casestatuslist(request):
    case_status = CaseStatus.objects.all().order_by("-id")
    context = {
        'case_status':case_status
    }
    return render(request,'Admin/mastermodule/Case/casestatuslist.html',context)


class casestatusEdit(LoginRequiredMixin,UpdateView):
    model = CaseStatus
    form_class = CaseStatusForm
    template_name = 'Admin/mastermodule/Case/casestatusupdate.html'
    success_url = '/Admin/CaseStatusMaster/'
    

class addfollowupPaymentstatus(LoginRequiredMixin,CreateView):
    model = followuppayment_status
    form_class = FollowUpPaymentStatusForm
    template_name = 'Admin/mastermodule/FollowUpPaymentStatus/addpaymentstatus.html'
    success_url = '/Admin/FollowUpPaymentStatus/'
    

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        messages.success(self.request, 'Follow-up payment status added successfully.')
        return super().form_valid(form)

@login_required
def followupPaymentstatus(request):
    followupstatus = followuppayment_status.objects.all().order_by("-id")
    context= {
        'followupstatus':followupstatus
    }
    return render(request,'Admin/mastermodule/FollowUpPaymentStatus/paymentlist.html',context)


class followupPaymentedit(LoginRequiredMixin,UpdateView):
    model = followuppayment_status
    form_class = FollowUpPaymentStatusForm
    template_name = 'Admin/mastermodule/FollowUpPaymentStatus/paymentupdate.html'
    success_url = reverse_lazy('followuppaymentstatus')

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        # Display a success message
        messages.success(self.request, 'Follow-up payement status updated successfully.')

        return super().form_valid(form)
    
class followupstatus(LoginRequiredMixin,ListView):
    model = followup_status
    template_name = 'Admin/mastermodule/FollowUpStatus/followupstatuslist.html'  
    context_object_name = 'followupstatus'
    
    def get_queryset(self):
        return followup_status.objects.all().order_by("-id")



class addfollowupstatus(LoginRequiredMixin,CreateView):
    model = followup_status
    form_class = FollowUpStatusForm
    template_name = 'Admin/mastermodule/FollowUpStatus/addfollowupstatus.html'
    success_url = '/Admin/FollowUpStatus/'
    

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        messages.success(self.request, 'Follow-up status added successfully.')
        return super().form_valid(form)



class followupEdit(LoginRequiredMixin,UpdateView):
    model = followup_status
    form_class = FollowUpStatusForm
    template_name = 'Admin/mastermodule/FollowUpStatus/followupupdate.html'
    success_url = reverse_lazy('followupstatus')

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"

        # Display a success message
        messages.success(self.request, 'Follow-up  status updated successfully.')

        return super().form_valid(form)
   
@login_required
def followuptype(request):
    followuptype = followupType.objects.all().order_by("-id")
    context = {
        'followuptype':followuptype
    }
    return render(request,'Admin/mastermodule/FollowUpType/followuptypelist.html',context)


class addfollowuptype(LoginRequiredMixin,CreateView):
    model = followupType
    form_class = FollowUpTypeForm
    template_name = 'Admin/mastermodule/FollowUpType/addfollowuptype.html'
    success_url = '/Admin/FollowUpType/'
    

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        messages.success(self.request, 'FollowUp Type added successfully.')
        return super().form_valid(form)

class followuptype_edit(LoginRequiredMixin,UpdateView):
    model = followupType
    form_class = FollowUpTypeForm
    template_name = 'Admin/mastermodule/FollowUpType/followuptypeupdate.html'
    success_url = reverse_lazy('followuptype')

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"

        # Display a success message
        messages.success(self.request, 'FollowUp  Type updated successfully.')

        return super().form_valid(form)

@login_required
def DocumentCategoryList(request):
    doc_Cat = DocumentCategory.objects.all().order_by("-id")
    context = {
        'doc_Cat':doc_Cat
    }
    return render(request,'Admin/mastermodule/DocumentCategory/documentcategorylist.html',context)

class addDocument_cat(LoginRequiredMixin,CreateView):
    model = DocumentCategory
    form_class = DocumentCategoryForm
    template_name = 'Admin/mastermodule/DocumentCategory/adddocumentcategory.html'
    success_url = reverse_lazy('DocumentCategorylist')
    # success_url = '/Admin/DocumentCategory/'
    

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        messages.success(self.request, 'Document Category added successfully.')
        return super().form_valid(form)


class editDocument_cat(LoginRequiredMixin,UpdateView):
    model = DocumentCategory
    form_class = DocumentCategoryForm
    template_name = 'Admin/mastermodule/DocumentCategory/documentcategoryupdate.html'
    success_url = reverse_lazy('DocumentCategorylist')

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"

        # Display a success message
        messages.success(self.request, 'FollowUp  Type updated successfully.')

        return super().form_valid(form)

@login_required
def currencyMaster(request):
    currency = Currency.objects.all().order_by("-id")
    context = {
        'currency':currency
    }
    return render(request,'Admin/mastermodule/Currency/currencylist.html',context)


class addcurrency(LoginRequiredMixin,CreateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'Admin/mastermodule/Currency/addcurrency.html'
    success_url = '/Admin/CurrencyMaster/'
    

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"
        messages.success(self.request, ' Currency added successfully.')
        return super().form_valid(form)


class editcurrency(LoginRequiredMixin,UpdateView):
    model = Currency
    form_class = CurrencyForm
    template_name = 'Admin/mastermodule/Currency/currencyupdate.html'
    success_url = reverse_lazy('currencyMaster')

    def form_valid(self, form):
        user = self.request.user
        form.instance.lastupdated_by = f"{user.first_name} {user.last_name}"

        # Display a success message
        messages.success(self.request, 'Currency updated successfully.')

        return super().form_valid(form)

import secrets
import string
@login_required
def add_employee(request):
    departments = Department.objects.all()
    branches = Branch.objects.all()
    groups = Group.objects.all()

    if request.method == "POST":
        department_id = request.POST.get('department_id')
        branch_id = request.POST.get('branch_id')
        group_id = request.POST.get('group_id')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        # generated_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        password="123456"
        country = request.POST.get('country')
        state = request.POST.get('state')
        city = request.POST.get('city')
        address = request.POST.get('address')
        zipcode = request.POST.get('zipcode')
        status = request.POST.get('status')
        files = request.FILES.get('file')
        
        # print("Generated Password:", generated_password)
        
        # Ensure that branch_id is provided
        if not branch_id:
            messages.warning(request, 'Branch ID is required')
            return redirect('add_employee')

        try:
            department = Department.objects.get(id=department_id)
            branchh = Branch.objects.get(id=branch_id)
            group = Group.objects.get(id=group_id)
            user = CustomUser.objects.create_user(
                username=email, first_name=firstname, last_name=lastname, email=email, password=password, user_type='3'
            )
           
            user.employee.department = department
            user.employee.branch = branchh
            user.employee.group = group
            user.employee.contact_no = contact
            user.employee.country = country
            user.employee.state = state
            user.employee.City = city
            user.employee.Address = address
            user.employee.zipcode = zipcode
            user.employee.status = status
            user.employee.file = files
            
            user.save()
            subject = "Congratulations! Your Account is Created"
            message = (
                f"Hello {firstname} {lastname},\n\n"
                f"Welcome to SSDC \n\n"
                f"Congratulations! Your account has been successfully created as an agent.\n\n"
                f" Your id is {email} and your password is {password}.\n\n"
                f" go to login : https://crm.theskytrails.com/ \n\n"
                f"Thank you for joining us!\n\n"
                f"Best regards,\nThe Sky Trails"
            )  # Customize this message as needed

            # Change this to your email
            print("messagess",message)
            recipient_list = [email]  # List of recipient email addresses

            send_mail(subject, message, from_email=None, recipient_list=recipient_list)
            messages.success(request, 'Employee Added Successfully Email sent Send!!')
            return redirect('all_employee')
            
        except Exception as e:
            messages.warning(request, str(e))
            return redirect('add_employee')

    context = {
        'department': departments,
        'branch': branches,
        'group':groups
    }
    return render(request, 'Admin/Employee/addemployee.html', context)


class all_employee(LoginRequiredMixin,ListView):
    model = Employee
    template_name = 'Admin/Employee/employeelist.html'  
    context_object_name = 'employee'
    
    def get_queryset(self):
        return Employee.objects.order_by("-id")
    

class view_employee(LoginRequiredMixin,ListView):
    model = Employee
    template_name = 'Admin/Employee/employeeview.html'  
    context_object_name = 'employee'
    
    def get_queryset(self):
        # Get the employee_id from the URL parameter
        employee_id = self.kwargs['employee_id']
        
        
        # Filter the queryset to get the employee with the specified ID
        queryset = Employee.objects.get(id=employee_id)
        
        
        return queryset
    
@login_required
def employee_update(request,pk):
    department = Department.objects.all()
    employee = Employee.objects.get(pk=pk)
    context = {
        'employee':employee,
        'department':department,
    }

    return render(request,'Admin/Employee/employeeupdate.html',context)
    
@login_required
def employee_update_save(request):
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
        return redirect("all_employee")
  
    
class SuccessStoriesCreateView(LoginRequiredMixin,CreateView):
    model = SuccessStories
    form_class = SuccessStoriesForm
    template_name = 'Admin/General/SuccessStories/addnewsuccessstory.html'
    success_url = reverse_lazy('SuccessStories_list')  
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        
        messages.success(self.request, 'SuccessStory Added Successfully.')
          
        return super().form_valid(form)
    
    
class SuccessStoriesListView(LoginRequiredMixin,ListView):
    model = SuccessStories
    template_name = 'Admin/General/SuccessStories/successstorieslist.html'  
    context_object_name = 'SuccessStories'
    
    def get_queryset(self):
        return SuccessStories.objects.order_by("-id")


class editSuccessStory(LoginRequiredMixin,UpdateView):
    model = SuccessStories
    form_class = SuccessStoriesForm
    template_name = 'Admin/General/SuccessStories/updatesuccessstory.html'
    success_url = reverse_lazy('SuccessStories_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'SuccessStory Updated Successfully.')

        return super().form_valid(form)
    
class NewsCreateView(LoginRequiredMixin,CreateView):
    model = News
    form_class = NewsForm
    template_name = 'Admin/General/News/addnews.html'
    success_url = reverse_lazy('News_list')  
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        
        messages.success(self.request, 'News Added Successfully.')
          
        return super().form_valid(form)
    
    
class NewsListView(LoginRequiredMixin,ListView):
    model = News
    template_name = 'Admin/General/News/newslist.html'  
    context_object_name = 'News'
    
    def get_queryset(self):
        return News.objects.order_by("-id")


class editNews(LoginRequiredMixin,UpdateView):
    model = News
    form_class = NewsForm
    template_name = 'Admin/General/News/updatenews.html'
    success_url = reverse_lazy('News_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'News Updated Successfully.')

        return super().form_valid(form)
    
    
class OfferBannerCreateView(LoginRequiredMixin,CreateView):
    model = OfferBanner
    form_class = OfferBannerForm
    template_name = 'Admin/General/OfferBanner/addofferbanner.html'
    success_url = reverse_lazy('OfferBanner_list') 
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        
        messages.success(self.request, 'OfferBanner Added Successfully.')
          
        return super().form_valid(form)
    
    
class OfferBannerListView(LoginRequiredMixin,ListView):
    model = OfferBanner
    template_name = 'Admin/General/OfferBanner/offerbannerlist.html'  
    context_object_name = 'OfferBanner'
    
    def get_queryset(self):
        return OfferBanner.objects.order_by("-id")


class editOfferBanner(LoginRequiredMixin,UpdateView):
    model = OfferBanner
    form_class = OfferBannerForm
    template_name = 'Admin/General/OfferBanner/updateofferbanner.html'
    success_url = reverse_lazy('OfferBanner_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'OfferBanner Updated Successfully.')

        return super().form_valid(form)
    
    

class PackageCreateView(LoginRequiredMixin,CreateView):
    model = Package
    form_class = PackageForm
    template_name = 'Admin/Package/addpackage.html'
    success_url = reverse_lazy('Package_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['visa_countries'] = VisaCountry.objects.all()
        context['visa_categories'] = VisaCategory.objects.all()
        context['visa_subcategories'] = VisaCategory.objects.all()
        context['image_form'] = PackageImageForm()  # Add a form for handling image uploads
        return context

    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        package = form.save()

        # Handle image uploads
        image_form = PackageImageForm(self.request.POST, self.request.FILES)
        xyz=self.request.FILES.getlist('image')
        print("hhjkhjkhjhj",xyz)
        if image_form.is_valid():
            for image in self.request.FILES.getlist('image'):
                # print("sdfghjk",image)
                PackageImage.objects.create(package=package, image=image)

        messages.success(self.request, 'Package Added Successfully.')
        return super().form_valid(form)

    
class PackageListView(LoginRequiredMixin,ListView):
    model = Package
    template_name = 'Admin/Package/packagelist.html'  
    context_object_name = 'Package'
    
    def get_queryset(self):
        return Package.objects.order_by("-id")


class editPackage(LoginRequiredMixin,UpdateView):
    model = Package
    form_class = PackageForm
    template_name = 'Admin/Package/packageupdate.html'
    success_url = reverse_lazy('Package_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'Package Updated Successfully.')

        return super().form_valid(form)
    
    
class CaseCategoryDocumentCreateView(LoginRequiredMixin,CreateView):
    
    model = CaseCategoryDocument
    form_class = CaseCategoryDocumentForm

    template_name = 'Admin/mastermodule/CaseCategoryDocument/addcasecategorydocument.html'
    success_url = reverse_lazy('CaseCategoryDocument_list')  
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['visa_countries'] = VisaCountry.objects.all()
        context['visa_categories'] = VisaCategory.objects.all()
        context['visa_subcategories'] = VisaCategory.objects.all()
        return context
    
    def form_valid(self, form):
        # Save the form instance without committing to the database yet
        instance = form.save(commit=False)

        # Access the selected_documents field from the submitted form
        # selected_documents = form.cleaned_data.get('selected_documents')
        # print("Selected Documents:", selected_documents)

        # Set the last_updated_by field
        instance.last_updated_by = self.request.user

        # Save the instance with selected_documents to the database
        instance.save()

        # Display a success message
        messages.success(self.request, 'CaseCategoryDocument Added Successfully.')
        
        return super().form_valid(form)   
    
class CaseCategoryDocumentListView(LoginRequiredMixin,ListView):
    model = CaseCategoryDocument
    template_name = 'Admin/mastermodule/CaseCategoryDocument/casecategorydocumentlist.html'  
    context_object_name = 'CaseCategoryDocument'

    def get_queryset(self):
        return CaseCategoryDocument.objects.order_by("-id")


class editCaseCategoryDocument(LoginRequiredMixin,UpdateView):
    model = CaseCategoryDocument
    form_class = CaseCategoryDocumentForm
    template_name = 'Admin/mastermodule/CaseCategoryDocument/casecategorydocumentupdate.html'
    success_url = reverse_lazy('CaseCategoryDocument_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'CaseCategoryDocument Updated Successfully.')

        return super().form_valid(form)
    
class FrontWebsiteEnquiryCreateView(LoginRequiredMixin,CreateView):
    model = FrontWebsiteEnquiry
    form_class = FrontWebsiteEnquiryForm
    template_name = 'Admin/FrontWebsiteEnquiry/addenquiry.html'
    success_url = reverse_lazy('FrontWebsiteEnquiry_list') 
    
    
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        user = self.request.user
        print("userrrrrrrrrrr",user)
        messages.success(self.request, 'FrontWebsiteEnquiry Added Successfully.')
        return super().form_valid(form)
    
    
class FrontWebsiteEnquiryListView(LoginRequiredMixin,ListView):
    model = FrontWebsiteEnquiry
    template_name = 'Admin/FrontWebsiteEnquiry/FrontWebsiteEnquirylist.html'  
    context_object_name = 'FrontWebsiteEnquiry'
    
    def get_queryset(self):
        return FrontWebsiteEnquiry.objects.order_by("-id")


class EnquiryCreateView(LoginRequiredMixin,CreateView):
    model = Enquiry
    form_class = EnquiryForm
    template_name = 'Admin/Enquiry/addenquiry.html'
    success_url = reverse_lazy('Enquiry_list')

    def form_valid(self, form):
        # Set the created_by field to the current user
        form.instance.created_by = self.request.user

        # Assign an employee to the new Enquiry
        self.assign_employee_to_enquiry(form.instance)

        # Display a success message
        messages.success(self.request, 'Enquiry Added Successfully.')

        return super().form_valid(form)

    def assign_employee_to_enquiry(self, enquiry):
        # Get all employees
        all_employees = Employee.objects.all()

        if all_employees:
            # Get the last assigned employee index from the session
            last_assigned_employee_index = self.request.session.get('last_assigned_employee_index', -1)

           
            next_index = (last_assigned_employee_index + 1) % all_employees.count()

            # Get the next employee to be assigned
            next_employee = all_employees[next_index]

            # Assign the employee to the enquiry
            enquiry.assign_to_employee = next_employee
            enquiry.save()

            # Update the last assigned employee index in the session
            self.request.session['last_assigned_employee_index'] = next_index
    



class EnquiryListView(LoginRequiredMixin,ListView):
    template_name = 'Admin/Enquiry/visaenquirylist.html'
    context_object_name = 'enquiries'  # Rename this to 'enquiries' to match your template

    
    def get_queryset(self):
        return Enquiry.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        # Get the default context data (data from the Enquiry model)
        context = super().get_context_data(**kwargs)

        current_datetime = timezone.now()
        context['current_datetime'] = current_datetime
        
        # Add data from the Notes model to the context
        context['notes'] = Notes.objects.all()
        # context['employee'] = Employee.objects.all()
        context['employee_queryset'] = Employee.objects.all()
        
        # employee_queryset = Employee.objects.all()
       
        

        return context
    
from django.db.models import Prefetch

@login_required
def view_enqlist(request, id):
    enq = Enquiry.objects.get(id=id)
    document = Document.objects.all()

    # doc_file = DocumentFiles.objects.get(enquiry_id=enq)

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
        "form": FollowUpForm(),
    }

    return render(request, "Admin/Enquiry/viewenquiry.html", context)


def delete_docfile(request, id):
    doc_id = DocumentFiles.objects.get(id=id)
    enq_id = Enquiry.objects.get(id=doc_id.enquiry_id.id)
    enqq = enq_id.id

    doc_id.delete()
    return redirect('view_enqlist', enqq)


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
                print("testingggg")

                doc.document_file = document_file
                doc.lastupdated_by = request.user
                doc.save()

                print("helloo querystet", doc)

                return redirect("view_enqlist", id=enq_id)
            else:
                print("create documentsfiles")

                documest_files = DocumentFiles.objects.create(
                    document_file=document_file,
                    document_id=document,
                    enquiry_id=enq,
                    lastupdated_by=request.user,
                )
                documest_files.save()
                return redirect("view_enqlist", id=enq_id)

        except Exception as e:
            pass
            print("erorrrrrrrrrrrrr", e)
 

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
def view_frontenqlist(request,id):
    enq = FrontWebsiteEnquiry.objects.get(id=id)
    context={
        "enq":enq
    }
    return render(request,'Admin/FrontWebsiteEnquiry/viewfrontenquiry.html',context)      
   

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
    
    return redirect('Enquiry_list')

@login_required
def assign_enquiry(request):
    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        emp_id = request.POST.get('emp_id')

        enq = Enquiry.objects.get(id=enq_id)
        employee = Employee.objects.get(id=emp_id)
        enq.lead_status="Active"
        enq.assign_to_employee = employee
        enq.save()


    return redirect('Enquiry_list')

@login_required
def lead_enquiry(request):
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
            return redirect('Enquiry_list')
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

    return redirect('Enquiry_list')
 


   

class enrolled_Application(LoginRequiredMixin,ListView):
    model = Enquiry
    template_name = (
        "Admin/ApplicationManagement/EnrolledApplication/enrolledapplicationlist.html"
    )
    context_object_name = "enquiry"

    def get_queryset(self):
        return Enquiry.objects.filter(
            Q(lead_status="Enrolled")
            | Q(lead_status="Inprocess")
            | Q(lead_status="Ready To Submit")
            | Q(lead_status="Appointment")
            | Q(lead_status="Ready To Collection")
            | Q(lead_status="Result")
            | Q(lead_status="Delivery")
            | Q(lead_status="Case Initiated")
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
        context["employee_queryset"] = Employee.objects.all()
        context["agent"] = Agent.objects.all()
        context["OutSourcingAgent"] = OutSourcingAgent.objects.all()
        context["enqenrolled"] = Enquiry.objects.filter(lead_status="Enrolled")

        # employee_queryset = Employee.objects.all()

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
    
    return redirect('enroll_application')

 
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


    return redirect('enroll_application')

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


    return redirect('enroll_application')


@login_required
def assign_employee(request):
    if request.method == "POST":
        enq_id = request.POST.get('enq_id')
        emp_id = request.POST.get('emp_id')

        enq = Enquiry.objects.get(id=enq_id)
        employee = Employee.objects.get(id=emp_id)
        enq.assign_to_employee = employee
        enq.save()


    return redirect('enroll_application')

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
        return redirect("edit_enrolled_application", id=id)

    return render(
        request,
        "Admin/ApplicationManagement/EnrolledApplication/editenrolledapplication.html",
        context,
    )



@login_required
def education_summary(request, id):
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
        return redirect("education_summary", id=id)

        # education_summary = Education_Summary.objects.create(enquiry_id=enq_id,country_of_education=educationcountry,highest_level_education=highest_education,grading_scheme=gradingscheme,grade_avg=gradeaverage,recent_college=recent_college)
    context = {"enquiry": enquiry, "education_summary": education_summary}
    return render(
        request,
        "Admin/ApplicationManagement/EnrolledApplication/Subforms/education-form.html",
        context,
    )



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

        return redirect("test_score", id=id)

    context = {
        "test_score": test_score,
        "enquiry_id": enquiry_id,
    }
    return render(
        request,
        "Admin/ApplicationManagement/EnrolledApplication/Subforms/test-score-form.html",
        context,
    )



@login_required
def delete_test_score(request, id):
    test_score = TestScore.objects.get(id=id)
    enquiry_id = test_score.enquiry_id.id
    test_score.delete()
    return redirect("test_score", id=enquiry_id)
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

            return redirect("background_information", id=id)
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

            return redirect("background_information", id=id)

    context = {
        "bk_info": bk_info,
        "enquiry_id": enquiry_id,
    }
    return render(
        request,
        "Admin/ApplicationManagement/EnrolledApplication/Subforms/background-form.html",
        context,
    )



@login_required
def documents(request,id):
    enquiry_id = Enquiry.objects.get(id=id)
    documents = ApplicationDocuments.objects.filter(enquiry_id=enquiry_id)
    context = {
        "enquiry_id":enquiry_id,
        "documents":documents,
    }
    return render(request, 'Admin/ApplicationManagement/EnrolledApplication/Subforms/document-form.html', context)

@login_required
def create_documents(request,id):
    enquiry_id = Enquiry.objects.get(id=id)
    
    if request.method == "POST":
        documentname = request.POST.get('documentname')
        comment = request.POST.get('comment')
        files = request.FILES.get('files')
        documts = ApplicationDocuments.objects.create(enquiry_id=enquiry_id,document_name=documentname,comments=comment,upload_documents=files)
        documts.save()
    return redirect('documents',id=id)

@login_required
def timeline(request,id):

    enquiry_id = Enquiry.objects.get(id=id)
    context = {
        "enquiry_id":enquiry_id
    }
    return render(request, 'Admin/ApplicationManagement/EnrolledApplication/Subforms/timeline-form.html', context)

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

            return redirect("workexperience", id=id)
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

            return redirect("workexperience", id=id)

    context = {
        "enquiry_id": enquiry_id,
        "work_exp": work_exp,
    }
    return render(
        request,
        "Admin/ApplicationManagement/EnrolledApplication/Subforms/workexperience-form.html",
        context,
    )



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
    return render(request,'Admin/ApplicationManagement/upload_to.html')



##################### Visa Case #####################


   
class ClientList(LoginRequiredMixin,ListView):
    model = Enquiry
    template_name = 'Admin/ApplicationManagement/VisaCases/visacaseslist.html'  
    context_object_name = 'enquiry'

    
    def get_queryset(self):
        queryset = Enquiry.objects.filter(lead_status="Case Initiated").order_by("-id")
        
        return queryset


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

    return render(request, 'Admin/ApplicationManagement/VisaCases/casestatus.html', {'enq_id': enq_id,'case_status':case_status,'application_status':application_status})

    # return redirect('update_case_status',id=id)

@login_required
def client_documents(request):
    return render(request,'Admin/ApplicationManagement/UserDocument/adduserdocument.html')


@login_required
def view_appointment(request,id):
    enq_id = Enquiry.objects.get(id=id)
    appointment = Appointment.objects.filter(enquiry_id=enq_id).order_by("-id")
    context = {
        'enq_id':enq_id,
        'appointment':appointment,
    }
    return render(request,'Admin/ApplicationManagement/VisaCases/appointmentlist.html',context)


def add_appointment(request,id):
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
            
            return redirect('view_appointment',id=id)  # Modify 'appointment_detail' to your URL pattern name
        except Exception as e:
            
            pass  


    return render(request,'Admin/ApplicationManagement/VisaCases/addappointment.html',{'enquiry':enquiry})
    


class loginlog(LoginRequiredMixin,ListView):
    model = LoginLog
    template_name = 'Admin/General/Loginlogs/loginlogs.html'
    context_object_name = 'loginlog'

    
    def get_queryset(self):
        return LoginLog.objects.exclude(user__user_type='1').order_by("-id")
    
  

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

            return render(request, 'Admin/General/Loginlogs/loginlogs.html', {'loginlog': loginlog_queryset})

    # If the request method is not POST or user_type is '1' (HOD), display all records except user_type '1'
    loginlog_queryset = LoginLog.objects.exclude(user__user_type='1')

    return render(request,'Admin/General/Loginlogs/loginlogs.html', {'loginlog': loginlog_queryset})   

@login_required
def add_agent(request):
    logged_in_user = CustomUser.objects.get(username=request.user.username)
    relevant_employees = Employee.objects.all()

    if request.method == "POST":
        type = request.POST.get('type')
        # ... (other form fields)

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
        assign_employee_id = request.POST.get('assign_employee')  

        existing_agent = CustomUser.objects.filter(username=email)

        try:
            if existing_agent:
                messages.warning(request, f'"{email}" already exists.')
                return redirect('add_agent')

            if type == "Outsourcing Partner":
                user = CustomUser.objects.create_user(username=email, first_name=firstname, last_name=lastname, email=email, password=password, user_type='5')
                logged_in_user = CustomUser.objects.get(username=request.user.username)

                user.outsourcingagent.type = type
                user.outsourcingagent.contact_no = contact
                user.outsourcingagent.country = country
                user.outsourcingagent.state = state
                user.outsourcingagent.City = city
                user.outsourcingagent.Address = address
                user.outsourcingagent.zipcode = zipcode
                user.outsourcingagent.activeinactive = activeinactive
                user.outsourcingagent.profile_pic = files
                user.outsourcingagent.registerdby = logged_in_user
                user.outsourcingagent.assign_employee_id = assign_employee_id
                user.save()

                subject = 'Congratulations! Your Account is Created'
                message = f'Hello {firstname} {lastname},\n\n' \
                    f'Welcome to SSDC \n\n' \
                    f'Congratulations! Your account has been successfully created as an Outsource Agent.\n\n' \
                    f' Your id is {email} and your password is {password}.\n\n' \
                    f' go to login : https://crm.theskytrails.com/Agent/Login/ \n\n' \
                    f'Thank you for joining us!\n\n' \
                    f'Best regards,\nThe Sky Trails'  # Customize this message as needed

            # Change this to your email
                recipient_list = [email]  # List of recipient email addresses

                send_mail(subject, message, from_email=None, recipient_list=recipient_list)

                messages.success(request, 'OutSource Agent Added Successfully')
                return redirect('all_outsource_agent')

            else:
                user = CustomUser.objects.create_user(username=email, first_name=firstname, last_name=lastname, email=email, password=password, user_type='4')
                logged_in_user = CustomUser.objects.get(username=request.user.username)

                user.agent.type = type
                user.agent.contact_no = contact
                user.agent.country = country
                user.agent.state = state
                user.agent.City = city
                user.agent.Address = address
                user.agent.zipcode = zipcode
                user.agent.activeinactive = activeinactive
                user.agent.profile_pic = files
                user.agent.registerdby = logged_in_user
                user.agent.assign_employee_id = assign_employee_id
                user.save()

                context = {
                    'employees': relevant_employees,
                }

                subject = 'Congratulations! Your Account is Created'
                message = f'Hello {firstname} {lastname},\n\n' \
                    f'Welcome to SSDC \n\n' \
                    f'Congratulations! Your account has been successfully created as an agent.\n\n' \
                    f' Your id is {email} and your password is {password}.\n\n' \
                    f' go to login : https://crm.theskytrails.com/Agent/Login/ \n\n' \
                    f'Thank you for joining us!\n\n' \
                    f'Best regards,\nThe Sky Trails'   # Customize this message as needed

            # Change this to your email
                recipient_list = [email]  # List of recipient email addresses

                send_mail(subject, message, from_email=None, recipient_list=recipient_list)

                messages.success(request, 'Agent Added Successfully')
                return redirect('all_agent')

        except Exception as e:
            messages.warning(request, e)

    context = {
        'employees': relevant_employees,
    }
    

    return render(request, 'Admin/agentmanagement/addagent.html', context)
 

class all_agent(LoginRequiredMixin, ListView):
    model = Agent
    template_name = 'Admin/agentmanagement/agentlist.html'  
    context_object_name = 'agent'

    def get_queryset(self):
        return Agent.objects.all().order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee_queryset'] = Employee.objects.all()
        return context
        



class all_outsource_agent(LoginRequiredMixin,ListView):
    model = OutSourcingAgent
    template_name = 'Admin/agentmanagement/agentoutsourcelist.html'  
    context_object_name = 'agentoutsource'

    def get_queryset(self):
        
        return OutSourcingAgent.objects.all().order_by("-id")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee_queryset'] = Employee.objects.all()
        return context
        
@login_required
def outsourceagent_agreement(request, id):
    
    outsource = OutSourcingAgent.objects.get(id=id)
    
    agrmnt = AgentAgreement.objects.filter(outsourceagent=outsource)
    context = {
        
        'outsource':outsource,
        'agrmnt':agrmnt
    }

    if request.method == "POST":

        
        outsource_id = request.POST.get('outsource_id')
        agreementname = request.POST.get('agreementname')
        agreement_file = request.FILES.get('agreement_file')

       
        
        outsource = OutSourcingAgent.objects.get(id=outsource_id)
        agreement = AgentAgreement.objects.create(outsourceagent=outsource, agreement_name=agreementname, agreement_file=agreement_file)
        agreement.save()
        print("Outsource agreement saved successfully")
        
        return redirect('outsourceagent_agreement',id=id)

    return render(request,'Admin/agentmanagement/outsourceagreement-form.html',context)

@login_required
def outsource_kyc(request,id):
    outsource = OutSourcingAgent.objects.get(id=id)
    kyc = AgentAgreement.objects.filter(outsourceagent=outsource)
    
    context = {
        'outsource':outsource,
        'kyc':kyc
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

    return render(request,'Admin/agentmanagement/agentoutsourcekyc-form.html',context)

@login_required
def agent_update(request,id):
    
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
        return redirect('all_agent')

    context = {
        'agent':agent,
        # 'outsource_agent':outsource_agent
        
    }
    return render(request,'Admin/agentmanagement/agentupdate.html',context)


@login_required
def outsourceagent_update(request,id):
    
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
        return redirect('all_outsource_agent')

    context = {
        
        'agent':agent
    }
    return render(request,'Admin/agentmanagement/outsourceagentupdate.html',context)

@login_required
def agent_agreement(request, id):
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
        'agrmnt':agrmnt
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
        return redirect('agent_agreement',id=id)

    return render(request,'Admin/agentmanagement/agreement-form.html',context)

@login_required
def agent_kyc(request,id):
    agent = Agent.objects.get(id=id)
    context = {
        'agent':agent
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

    return render(request,'Admin/agentmanagement/kyc-form.html',context)

@login_required
def agent_status_update(request):
    
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
            return redirect('all_agent')  # Redirect to some appropriate URL
        # agent.status = status
        # return redirect('all_agent')


    return redirect('all_agent')


class DepartmentCreateView(LoginRequiredMixin,CreateView):

    model = Department
    form_class = DepartmentForm
    template_name = 'Admin/Rolesmanagement/addrole.html'
    success_url = reverse_lazy('Department_list') 
    
    def form_valid(self, form):
        # Check if a Department with the same name already exists
        name = form.cleaned_data.get("name")
        if Department.objects.filter(name=name).exists():
            messages.error(
                self.request,
                "This name already exists. Please choose a different name.",
            )
            return self.form_invalid(form)

        return super().form_valid(form)
    
    
    
class DepartmentListView(LoginRequiredMixin,ListView):
    model = Department
    template_name = 'Admin/Rolesmanagement/rolelist.html'  
    context_object_name = 'role'
    
    def get_queryset(self):
        return Department.objects.order_by("-id")
    
class editDepartment(LoginRequiredMixin,UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'Admin/Rolesmanagement/roleupdate.html'
    success_url = reverse_lazy('Department_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'Department Updated Successfully.')

        return super().form_valid(form)


@login_required(login_url='/') 
def ChangePassword(request):
    user = request.user
    admin = Admin.objects.get(users=user)
    
    if request.method == "POST":
        old_psw = request.POST.get('old_password')
        newpassword = request.POST.get('newpassword')
        confirmpassword = request.POST.get('confirmpassword')
        
        if check_password(old_psw, admin.users.password):
            if newpassword == confirmpassword:
                # Set the new password for the user
                admin.users.set_password(newpassword)
                admin.users.save()
                messages.success(request,"Password changed successfully Please Login Again !!")
                return HttpResponseRedirect(reverse("ChangePassword"))
            else:
                messages.success(request,"New passwords do not match")
                return HttpResponseRedirect(reverse("ChangePassword"))
                
        else:
            # print("Old password is not correct")
            messages.warning(request,'Old password is not correct')
            
       
    return render(request, 'Admin/ChangePassword/changepassword.html')

class CreateGroupView(LoginRequiredMixin,CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'Admin/mastermodule/Manage Groups/addgroup.html'  # Update with your template name
    success_url = reverse_lazy('Group_list') 
    
    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.create_by = self.request.user

        # Display a success message
        messages.success(self.request, 'Group Added Successfully.')

        return super().form_valid(form)
    
class GroupListView(LoginRequiredMixin,ListView):
    model = Group
    template_name = 'Admin/mastermodule/Manage Groups/grouplist.html'  
    context_object_name = 'group'
    
    def get_queryset(self):
        return Group.objects.order_by("-id")
    
class editGroup(LoginRequiredMixin,UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'Admin/mastermodule/Manage Groups/updategroup.html'
    success_url = reverse_lazy('Group_list')

    def form_valid(self, form):
        # Set the lastupdated_by field to the current user's username
        form.instance.lastupdated_by = self.request.user

        # Display a success message
        messages.success(self.request, 'Group Updated Successfully.')

        return super().form_valid(form)
    
class all_appointment(LoginRequiredMixin,ListView):
    model = Appointment
    template_name = 'Admin/Appointment/appointmentlist.html'
    context_object_name = 'appointment'
    
    def get_queryset(self):
        return Appointment.objects.order_by("-id")
    
@login_required
def AssignRoleView(request):
    if request.method == "POST":
        department_id = request.POST.get('department')
        menu_choices = request.POST.getlist('menu_choice')
        employee_ids = request.POST.getlist('employee')

        try:
            department = Department.objects.get(id=department_id)
            employees = Employee.objects.filter(id__in=employee_ids)
            

            role_assignment = AssignRoles.objects.create(department=department)

            for menu_id in menu_choices:
                menu = Menu.objects.get(id=menu_id)
                role_assignment.menu_name.add(menu)

                # If this menu has submenus, add them too
                

            for employee in employees:
                role_assignment.employee.add(employee)

            messages.success(request, 'Role assigned successfully.')
            return redirect('assignrolelist')

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

    return render(request, 'Admin/permission.html', context)

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

    return render(request, 'Admin/Rolesmanagement/assign_roles_list.html', context)

@login_required
def AssignUpdateView(request,pk):
    assign_roles = AssignRoles.objects.get(id=pk)
    department = Department.objects.all()
    menu = Menu.objects.all()

    employees = Employee.objects.filter(id__in=assign_roles.employee.values_list('id', flat=True))
    
    
    context = {
        'assign_roles':assign_roles,
        'department':department,
        'menu':menu,
        'employee':employees
    }
    return render(request, 'Admin/Rolesmanagement/assign_update.html', context)


@login_required
def AssignUpdatesave(request):
    if request.method == "POST":
        assign_id = request.POST.get('assign_id')
        department_id = request.POST.get('department_id')
        menu_ids = request.POST.getlist('menu_id')
        employee_ids = request.POST.getlist('employee_id')

        department = Department.objects.get(id=department_id)
        
        # Assuming that menu_name is a ManyToManyField, you should use get_list_or_404
        menus = Menu.objects.filter(id__in=menu_ids)
        
        # Assuming that employee is a ManyToManyField, you should use get_list_or_404
        employees = Employee.objects.filter(id__in=employee_ids)

        assign_role = get_object_or_404(AssignRoles, id=assign_id)

        assign_role.department = department
        assign_role.menu_name.set(menus)
        assign_role.employee.set(employees)
        assign_role.save()
        
        messages.success(request, 'Assign Roles Updated Successfully!!')
        return redirect('assignrolelist')

class addbranch(LoginRequiredMixin,CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'Admin/mastermodule/Branch/addbranch.html'
    success_url = reverse_lazy('branchlist') 
    
    def form_valid(self, form):
        form.instance.last_updated_by = self.request.user
        
        messages.success(self.request, 'Branch Added Successfully.')
          
        return super().form_valid(form)

@login_required
def branchlist(request):
    branch = Branch.objects.all().order_by("-id")
    context = {
        'branch':branch
    }
    return render(request,'Admin/mastermodule/Branch/branchlist.html',context)

@login_required
def delete_branch(request, id):
    branch = get_object_or_404(Branch, id=id)
    branch.delete()
    return redirect('branchlist')

@login_required
def delete_group(request, id):
    group = get_object_or_404(Group, id=id)
    group.delete()
    return redirect('Group_list')

@login_required
def delete_role(request, id):
    role = get_object_or_404(Department, id=id)
    role.delete()
    return redirect('Department_list')

@login_required
def delete_appointment(request, id):
    appointment = get_object_or_404(Appointment, id=id)
    appointment.delete()
    return redirect('all_appointment')

@login_required  
def delete_casecategorydocument(request, id):
    casecategorydocument = get_object_or_404(CaseCategoryDocument, id=id)
    casecategorydocument.delete()
    return redirect('CaseCategoryDocument_list')

@login_required
def delete_package(request, id):
    package = get_object_or_404(Package, id=id)
    package.delete()
    return redirect('Package_list')

@login_required
def delete_offerbanner(request, id):
    offerbanner = get_object_or_404(OfferBanner, id=id)
    offerbanner.delete()
    return redirect('OfferBanner_list')

@login_required  
def delete_news(request, id):
    news = get_object_or_404(News, id=id)
    news.delete()
    return redirect('News_list')

@login_required
def delete_successstories(request, id):
    successstories = get_object_or_404(SuccessStories, id=id)
    successstories.delete()
    return redirect('SuccessStories_list')

@login_required
def delete_currency(request, id):
    currency = get_object_or_404(Currency, id=id)
    currency.delete()
    return redirect('currencyMaster')

@login_required
def delete_documentcategory(request, id):
    documentcategory = get_object_or_404(DocumentCategory, id=id)
    documentcategory.delete()
    return redirect('DocumentCategorylist')

@login_required
def delete_followuptype(request, id):
    followuptype = get_object_or_404(followupType, id=id)
    followuptype.delete()
    return redirect('followuptype')

@login_required
def delete_followupstatus(request, id):
    followupstatus = get_object_or_404(followup_status, id=id)
    followupstatus.delete()
    return redirect('followupstatus')

@login_required
def delete_followuppayment(request, id):
    followuppayment = get_object_or_404(followuppayment_status, id=id)
    followuppayment.delete()
    return redirect('followuppaymentstatus')

@login_required
def delete_casestatus(request, id):
    casestatus = get_object_or_404(CaseStatus, id=id)
    casestatus.delete()
    return redirect('casestatuslist')

@login_required
def delete_courieraddress(request, id):
    courieraddress = get_object_or_404(CourierAddress, id=id)
    courieraddress.delete()
    return redirect('viewcourieraddress_list')

@login_required
def delete_document(request, id):
    document = get_object_or_404(Document, id=id)
    document.delete()
    return redirect('document_list')

@login_required
def delete_subcategory(request, id):
    subcategory = get_object_or_404(VisaSubcategory, id=id)
    subcategory.delete()
    return redirect('subcategory_list')

@login_required
def delete_category(request, id):
    category = get_object_or_404(VisaCategory, id=id)
    category.delete()
    return redirect('category_list')

@login_required
def delete_country(request, id):
    country = get_object_or_404(VisaCountry, id=id)
    country.delete()
    return redirect('visa_countrylist')


@login_required
def import_employee(request):
    if request.method == "POST":
        file = request.FILES['file']

        try:
            df = pd.read_excel(file)
            for row in df.itertuples(index=False):
                branch_id = row[5]
                department_id = row[6]
                email = row[3]
                first_name = row[1]

                # Check if an employee with the same email already exists
                existing_employee = Employee.objects.filter(users__email=email).first()

                if existing_employee:
                    # Employee with the same email already exists, skip this row
                    print(f"Employee with email {email} already exists. It was not imported.")
                else:
                    # Get the Branch and Department instances based on their IDs
                    branch = Branch.objects.get(id=branch_id)
                    department = Department.objects.get(id=department_id)

                    # Create the Employee instance with the associated CustomUser
                    custom_user, created = CustomUser.objects.get_or_create(email=email)
                    custom_user.first_name = first_name
                    custom_user.last_name = row[2]
                    custom_user.contact_no = row[4]
                    custom_user.set_password(row[7])
                    custom_user.username = row[3]
                    custom_user.save()

                    employee = Employee(
                        users=custom_user,
                        branch=branch,
                        department=department,
                    )

                    # Save the Employee instance
                    employee.save()
                    print(f"User with email {email} imported successfully.")

            print("Data imported successfully.")
        except Exception as e:
            messages.warning(request, f"Error importing data: {e}")
            print(f"Error importing data: {e}")

    # Redirect to a specific view or template after importing
    return redirect('all_employee')


# ################################################## IMPORT VIEWS #############################################



@login_required
def import_employee(request):
    if request.method == "POST":
        file = request.FILES['file']

        try:
            df = pd.read_excel(file)
            for row in df.itertuples(index=False):
                branch_id = row[5]
                department_id = row[6]
                email = row[3]
                first_name = row[1]  # Get first_name from Excel data

                # Get or create the CustomUser instance based on the email
                custom_user, _ = CustomUser.objects.get_or_create(email=email)

                # Get the Branch and Department instances based on their IDs
                branch = Branch.objects.get(id=branch_id)
                department = Department.objects.get(id=department_id)

                # Create the Employee instance with the associated CustomUser
                employee = Employee(
                    users=custom_user,
                    branch=branch,
                    department=department,
                )
                # Set the first_name, last_name, email, contact_no, and password
                employee.users.first_name = first_name
                employee.users.last_name = row[2]
                employee.users.email = email
                employee.users.contact_no = row[4]
                employee.users.password = row[7]
                employee.users.username = row[3]

                # Save both the CustomUser and Employee instances
                employee.users.save()
                employee.save()

            print("Data imported successfully.")
        except Exception as e:
            print(f"Error importing data: {e}")

    # Redirect to a specific view or template after importing
    return redirect('all_employee')

@login_required
def import_department(request):
    if request.method == "POST":
        file = request.FILES['file']
        path = str(file)
        print(f'File path: {settings.BASE_DIR}/{path}')

        try:
            df = pd.read_excel(file)
            
            for row in df.iloc[2:].itertuples(index=False):
                dep = row[1].strip()  # Remove leading/trailing whitespace
                
                # Check if the country already exists in the database
                department, created = Department.objects.get_or_create(name=dep)
                
                # If created is True, it means the country didn't exist and was added
                if created:
                    department.save()
            

            print("Data imported successfully.")
            messages.success(request,'Data Imported Successfully!!')

        except Exception as e:
            messages.warning(request,e)
            print(f"Error importing data: {e}")
            return redirect('Department_list')
    return redirect('Department_list')

@login_required
def import_branch(request):
    if request.method == "POST":
        file = request.FILES['file']
        path = str(file)
        print(f'File path: {settings.BASE_DIR}/{path}')

        try:
            df = pd.read_excel(file)
            
            for row in df.iloc[2:].itertuples(index=False):
                branchname = row[1].strip()  # Remove leading/trailing whitespace
                
                # Check if the country already exists in the database
                branch_id, created = Branch.objects.get_or_create(branch_name=branchname)
                
                # If created is True, it means the country didn't exist and was added
                if created:
                    branch_id.save()
            

            print("Data imported successfully.")
            messages.success(request,'Data Imported Successfully!!')

        except Exception as e:
            messages.warning(request,e)
            print(f"Error importing data: {e}")
            return redirect('branchlist')
    return redirect('branchlist')

@login_required
def import_casestatus(request):
    if request.method == "POST":
        file = request.FILES['file']
        path = str(file)
        print(f'File path: {settings.BASE_DIR}/{path}')
        
        try:
            df = pd.read_excel(file)
            
            for row in df.iloc[2:].itertuples(index=False):
                casestatus = row[1].strip()  # Remove leading/trailing whitespace
                
                # Check if the country already exists in the database
                casestatus, created = CaseStatus.objects.get_or_create(case_status=casestatus)
                
                # If created is True, it means the country didn't exist and was added
                if created:
                    casestatus.save()
            

            print("Data imported successfully.")
            messages.success(request,'Data Imported Successfully!!')

        except Exception as e:
            messages.warning(request,e)
            print(f"Error importing data: {e}")
            return redirect('casestatuslist')
    return redirect('casestatuslist')

@login_required
def import_paymentstatus(request):
    if request.method == "POST":
        file = request.FILES['file']
        path = str(file)
        print(f'File path: {settings.BASE_DIR}/{path}')

        try:
            df = pd.read_excel(file)
            
            for row in df.iloc[2:].itertuples(index=False):
                followupstatus = row[1].strip()  # Remove leading/trailing whitespace
                
                # Check if the country already exists in the database
                paymentstatus, created = followuppayment_status.objects.get_or_create(followup_status=followupstatus)
                
                # If created is True, it means the country didn't exist and was added
                if created:
                    paymentstatus.save()
            

            print("Data imported successfully.")
            messages.success(request,'Data Imported Successfully!!')

        except Exception as e:
            messages.warning(request,e)
            print(f"Error importing data: {e}")
            return redirect('followuppaymentstatus')
    return redirect('followuppaymentstatus')

@login_required
def import_country(request):
    if request.method == "POST":
        file = request.FILES['file']
        path = str(file)
        print(f'File path: {settings.BASE_DIR}/{path}')

        try:
            df = pd.read_excel(file)
            
            for row in df.iloc[2:].itertuples(index=False):
                country_name = row[1].strip()  # Remove leading/trailing whitespace
                
                # Check if the country already exists in the database
                visa_country, created = VisaCountry.objects.get_or_create(country=country_name)
                
                # If created is True, it means the country didn't exist and was added
                if created:
                    visa_country.save()
            

            print("Data imported successfully.")
            messages.success(request,'Data Imported Successfully!!')

        except Exception as e:
            messages.warning(request,e)
            print(f"Error importing data: {e}")
            return redirect('visa_countrylist')
    return redirect('visa_countrylist')

@login_required
def document_modal_view(request):
    if request.method == "POST":
        category = request.POST.get('category')
        status = request.POST.get('status')
        

        documents = DocumentCategory.objects.create(Document_category=category,status=status)
        documents.save()
            
    
    return redirect('add_document')


class FAQCreateView(LoginRequiredMixin,CreateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'Admin/FAQ/addfaq.html'
    success_url = reverse_lazy('faqlist') 
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        messages.success(self.request, 'FAQ Added Successfully.')
          
        return super().form_valid(form)
    
class FAQListView(LoginRequiredMixin,ListView):
    model = FAQ
    template_name = 'Admin/FAQ/faqlist.html'
    context_object_name = 'FAQs'
    
    def get_queryset(self):
        return FAQ.objects.order_by("-id")

class FAQUpdateView(LoginRequiredMixin,UpdateView):
    model = FAQ
    form_class = FAQForm
    template_name = 'Admin/FAQ/updatefaq.html'  
    success_url = reverse_lazy('faqlist')

    def form_valid(self, form):

        # Display a success message
        messages.success(self.request, 'FAQ updated successfully.')

        return super().form_valid(form)

@login_required
def delete_faq(request, id):
    faq = get_object_or_404(FAQ, id=id)
    faq.delete()
    return redirect('faqlist')


######################################  FOLLOWUP LIST  ############################################

class enquiryfollowupList(LoginRequiredMixin,ListView):
    model = FollowUp
    template_name = "Admin/followups/enquiryfollowups.html"
    context_object_name = 'enquiryfollowup'
    
    
class EnquiryFollowupUpdate(LoginRequiredMixin,UpdateView):
    model = FollowUp
    form_class = FollowUpForm
    template_name = 'Admin/Enquiry/editfollowup.html'  
    success_url = reverse_lazy('enquiryfollowup')

    def form_valid(self, form):

        form.instance.created_by = self.request.user
        messages.success(self.request, 'FollowUp updated successfully.')

        return super().form_valid(form)

@login_required
def delete_followup(request, id):
    followup = get_object_or_404(FollowUp, id=id)
    followup.delete()
    return redirect('enquiryfollowup')
    
    
class EnrolledApplicationView(LoginRequiredMixin,DetailView):
    model = Enquiry  
    template_name = "Admin/ApplicationManagement/EnrolledApplication/viewenrolledapplication.html"
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
   

    country_data = Enquiry.objects.values("Visa_country__country").annotate(
        total_inquiries=Count("id")
    )
    
    
    country_data_list = list(country_data)

    return JsonResponse(country_data_list, safe=False)


def leads_detail(request, country_name):
    enquiry = Enquiry.objects.filter(Visa_country__country=country_name)
   
    
    context = {"enquiries": enquiry}
    return render(request, "Admin/CountryWiseLeads/enquiry_list.html", context)

    
@login_required
def activity_log_view(request):
    activity_logs = ActivityLog.objects.all().order_by("-id")

    context = {
        'activity_logs': activity_logs
    }

    return render(request, 'Admin/Activity Logs/activitylogs.html', context)
    
    
    
    
@login_required
def assign_to_employeee(request):
    if request.method == "POST":
        agent_id = request.POST.get('agent_id')
       
        emp_id = request.POST.get('emp_id')

        agent = Agent.objects.get(id=agent_id)
        employee = Employee.objects.get(id=emp_id)

        
        agent.assign_employee = employee
        agent.save()

    return redirect('all_agent')


@login_required
def assign_to_outemployeee(request):
    if request.method == "POST":
        outsource_id = request.POST.get('outsource_id')
       
        emp_id = request.POST.get('emp_id')

        outsource = OutSourcingAgent.objects.get(id=outsource_id)
        employee = Employee.objects.get(id=emp_id)

        
        outsource.assign_employee = employee
        outsource.save()

    return redirect('all_outsource_agent')
    
    

class CreateChatGroupView(LoginRequiredMixin, CreateView):
    model = ChatGroup
    form_class = ChatGroupForm
    template_name = "chat/chatgroup.html"  # Update with your template name
    success_url = reverse_lazy("ChatGroup_list")

    def form_valid(self, form):
        chat_group = form.save(commit=False)

        # Set the create_by field to the current user
        chat_group.create_by = self.request.user

        # Save the ChatGroup instance to get an ID
        chat_group.save()

        # Add the creator to the group members
        chat_group.group_member.add(self.request.user)

        # Display a success message
        messages.success(self.request, "ChatGroup Added Successfully.")
        return super().form_valid(form)


class ChatGroupListView(LoginRequiredMixin, ListView):
    model = ChatGroup
    template_name = "chat/grouplist.html"
    context_object_name = "group"


class editGroupChat(LoginRequiredMixin, UpdateView):
    model = ChatGroup
    form_class = ChatGroupForm
    template_name = "chat/updategroup.html"
    success_url = reverse_lazy("ChatGroup_list")

    def form_valid(self, form):
        form.instance.lastupdated_by = self.request.user

        messages.success(self.request, "ChatGroup Updated Successfully.")

        return super().form_valid(form)
        
        
class profileview(TemplateView,LoginRequiredMixin):
    template_name = "Admin/profile.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        leads = Enquiry.objects.all()
        employee = Employee.objects.all()
        agent = Agent.objects.all()
        
        user = self.request.user

        context['first_name'] = user.first_name
        context['last_name'] = user.last_name
        context['email'] = user.email
        context['contact'] = user.admin.contact_no
        if hasattr(user, 'get_user_type_display'):
            context['user_type'] = user.get_user_type_display()
        context['leads'] = leads
        context['employee'] = employee
        context['agent'] = agent

        return context
    

@login_required
def edit_profile(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')

        admin_instance = Admin.objects.get(users=request.user)
        
        admin_instance.users.first_name = first_name
        admin_instance.users.last_name = last_name
        admin_instance.users.email = email
        admin_instance.contact_no = contact

        
        admin_instance.users.save()
        admin_instance.save()

        
        return redirect("profile")
        

    return render(request, 'Admin/profile.html')
        
         


    
    