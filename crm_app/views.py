import requests
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from .forms import LoginForm
from django.views.generic import TemplateView
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django.utils import timezone
from .models import LoginLog
from .models import CustomUser
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from rest_framework import viewsets
from .models import Booking, ChatGroup, ChatMessage,FrontWebsiteEnquiry,VisaCountry,VisaCategory,Admin, Employee,Agent
from .serializers import BookingSerializer,FrontWebsiteSerializer
from rest_framework.viewsets import ViewSet, ModelViewSet
import random
from django.db.utils import IntegrityError
from django.core.mail import send_mail




class DashboardView(TemplateView):
    template_name = "SuperadminDashboard/index2.html"

class TravelDashboard(TemplateView):
    template_name = "dashboard/index2.html"
        



def get_public_ip():
    try:
        response = requests.get("https://api64.ipify.org?format=json")
        data = response.json()
        return data["ip"]
    except Exception as e:
        # Handle the exception (e.g., log the error)
        return None
        
        
def agent_signup(request):
    if request.method == "POST":
        user_type = request.POST.get("type")
        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        contact_no = request.POST.get("contact_no")
        password = request.POST.get("password")

        existing_agent = CustomUser.objects.filter(email=email)

        try:
            if existing_agent:
                messages.warning(request, f'"{email}" already exists.')
                return render(request, "account/agent_signup.html")

            if user_type == "Outsourcing partner":
                user = CustomUser.objects.create_user(
                    username=email,
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    password=password,
                    user_type="5",
                )

                user.outsourcingagent.type = user_type
                user.outsourcingagent.contact_no = contact_no

                user.save()
                messages.success(request, "OutsourceAgent Added Successfully")
                
                subject = "Congratulations! Your Account is Created"
                message = (
                    f"Hello {firstname} {lastname},\n\n"
                    f"Welcome to SSDC \n\n"
                    f"Congratulations! Your account has been successfully created as an Outsource Agent.\n\n"
                    f" Your id is {email} and your password is {password}.\n\n"
                    f" go to login : https://crm.theskytrails.com \n\n"
                    f"Thank you for joining us!\n\n"
                    f"Best regards,\nThe Sky Trails"
                )  # Customize this message as needed

                # Change this to your email
                recipient_list = [email]  # List of recipient email addresses

                send_mail(
                    subject, message, from_email=None, recipient_list=recipient_list
                )
                
                request.session["username"] = email
                request.session["password"] = password

            else:
                user2 = CustomUser.objects.create_user(
                    username=email,
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    password=password,
                    user_type="4",
                )

                user2.agent.type = user_type
                user2.agent.contact_no = contact_no

                user2.save()

                messages.success(request, "Agent Added Successfully")
                
                subject = "Congratulations! Your Account is Created"
                message = (
                    f"Hello {firstname} {lastname},\n\n"
                    f"Welcome to SSDC \n\n"
                    f"Congratulations! Your account has been successfully created as an agent.\n\n"
                    f" Your id is {email} and your password is {password}.\n\n"
                    f" go to login : https://crm.theskytrails.com \n\n"
                    f"Thank you for joining us!\n\n"
                    f"Best regards,\nThe Sky Trails"
                )  # Customize this message as needed

                # Change this to your email
                recipient_list = [email]  # List of recipient email addresses

                send_mail(
                    subject, message, from_email=None, recipient_list=recipient_list
                )
                
                request.session["username"] = email
                request.session["password"] = password

            # Send OTP via SMS for both user types
            random_number = random.randint(0, 999)
            send_otp = str(random_number).zfill(4)
            request.session["sendotp"] = send_otp

            if user_type == "4":
                contact_no = user2.agent.contact_no
            elif user_type == "5":
                contact_no = user.outsourcingagent.contact_no

            url = "http://sms.txly.in/vb/apikey.php"
            payload = {
                "apikey": "lbwUbocDLNFjenpa",
                "senderid": "SKTRAL",
                "templateid": "1007338024565017323",
                "number": contact_no,
                "message": f"Use this OTP {send_otp} to login to your theskytrails account",
            }
            response = requests.post(url, data=payload)

            return redirect("verify_otp")

        except Exception as e:
            # Handle exceptions if any
            messages.error(request, f"An error occurred: {str(e)}")

    return render(request, "account/agent_signup.html")




def CustomLoginView(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        request.session["username"] = username
        request.session["password"] = password

        try:
            user = CustomUser.objects.get(username=username)

            if check_password(password, user.password):
                user_type = user.user_type

                if user_type == "1":
                    # If user_type is "1" (HOD), log in directly
                    user = authenticate(request, username=username, password=password)

                    if user is not None:
                        login(request, user)
                        return redirect("/crm/dashboard/")

                elif user_type in ("2", "3","4","5"):
                    public_ip = get_public_ip()
                    LoginLog.objects.create(
                        user=user,
                        ip_address=public_ip if public_ip else None,
                        login_datetime=timezone.now(),
                        # date = timezone.now()
                    )
                    # If user_type is "2" (Admin) or "3" (Employee), proceed with OTP verification
                    request.session["username"] = username
                    request.session["password"] = password
                    user_id = user.id
                    mob = ""
                    customeruser = CustomUser.objects.get(id=user_id)
                    usr_type = customeruser.user_type
                    if user_type == "2":
                        mob = customeruser.admin.contact_no

                    if user_type == "3":
                        mob = customeruser.employee.contact_no
                        
                    if user_type == "4":
                        mob = customeruser.agent.contact_no
                        
                    if user_type == "5":
                        mob = customeruser.outsourcingagent.contact_no

                    random_number = random.randint(0, 999)
                    send_otp = str(random_number).zfill(4)
                    request.session["sendotp"] = send_otp
                    print("senddddd ot", send_otp)
                    url = "http://sms.txly.in/vb/apikey.php"
                    payload = {
                        "apikey": "lbwUbocDLNFjenpa",
                        "senderid": "SKTRAL",
                        "templateid": "1007338024565017323",
                        "number": mob,
                        "message": f"Use this OTP {send_otp} to login to your. theskytrails account",
                    }
                    response = requests.post(url, data=payload)

                    # send_otp_and_redirect(request, user_id, user_type)
                    # return redirect("verify_otp")
                    return redirect("verify_otp")
                else:
                    return HttpResponse("User type not supported")

            else:
                messages.error(request, "Username and Password Incorrect")
                return redirect("login")

        except CustomUser.DoesNotExist:
            messages.error(request, "User Does Not Exist")
            return redirect("login")
            # return HttpResponse("Username and Password Incorrect")

    return render(request, "account/newlogin.html")



def verify_otp(request):
    if request.method == "POST":
        # username = request.session.get("username")
        username = request.session.get(
            "username", "Default value if key does not exist"
        )
        password = request.session.get(
            "password", "Default value if key does not exist"
        )
        sendotp = request.session.get("sendotp", "Default value if key does not exist")

        print("sendddd otp is:", sendotp)

        submitted_otp = request.POST.get("submitted_otp")

        if submitted_otp == sendotp:
        #if submitted_otp == "1234":
            print("successs")
            user = authenticate(request, username=username, password=password)
            print("usersssssssssss", user)
            if user != None:
                print("workingg")
                login(request, user)
                user_type = user.user_type
                if user_type == "1":
                    return redirect("dashboard")
                if user_type == "2":
                    return redirect("travel_dashboards")
                if user_type == "3":
                    return redirect("employee_dashboard")
                if user_type == "4":
                    return redirect("agent_dashboard")
                if user_type == "5":
                    return redirect("agent_dashboard")

                public_ip = get_public_ip()
                LoginLog.objects.create(
                    user=user,
                    ip_address=public_ip if public_ip else None,
                    login_datetime=timezone.now(),
                    # date = timezone.now()
                )

        else:
            messages.error(request, "Wrong Otp")
            print("not success")

    return render(request, "account/otp_verify.html")



def forgot_psw(request):
    if request.method == "POST":
        mob_no = request.POST.get("mob_no")
        user = None
        try:
            admin_profile = Admin.objects.get(contact_no=mob_no)
            user = admin_profile.users
            request.session["admin_profile"] = admin_profile.id

        except Admin.DoesNotExist:
            pass

        try:
            employee_profile = Employee.objects.get(contact_no=mob_no)
            user = employee_profile.users
        except Employee.DoesNotExist:
            pass

        try:
            agent_profile = Agent.objects.get(contact_no=mob_no)
            user = agent_profile.users
        except Agent.DoesNotExist:
            pass

        if user is not None:
            request.session["user_id"] = user.id

            random_number = random.randint(0, 999)
            forgetsend_otp = str(random_number).zfill(4)
            request.session["forgotsendotp"] = forgetsend_otp

            url = "http://sms.txly.in/vb/apikey.php"
            payload = {
                "apikey": "lbwUbocDLNFjenpa",
                "senderid": "SKTRAL",
                "templateid": "1007338024565017323",
                "number": mob_no,
                "message": f"Use this OTP {forgetsend_otp} to login to your. theskytrails account",
            }
            response = requests.post(url, data=payload)

            return redirect("forget_otp")

        else:
            messages.error(request, "Mobile number does not match any user.")

    return render(request, "Authentication/forgot_psw.html")

    # return render(request, "Authentication/forgot_psw.html")


def forget_otp(request):
    sendotp = request.session.get(
        "forgotsendotp", "Default value if key does not exist"
    )
    print("sendd otp", sendotp)
    if request.method == "POST":
        submitted_otp = request.POST.get("submitted_otp")
        if submitted_otp == sendotp:
            return redirect("reset_psw")
        else:
            messages.error(request, "OTP not matched..")

    return render(request, "Authentication/forget_otp_verify.html")


from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate


def reset_psw(request):
    user_id = request.session.get("user_id", "Default value if key does not exist")
    
   
   

    if request.method == "POST":
        new_psw = request.POST.get("new_psw")
        confirm_psw = request.POST.get("confirm_psw")

        if new_psw == confirm_psw:
            user_instance = CustomUser.objects.get(id=user_id)

            try:
                # Use set_password to properly hash and save the password
                # print("Before setting password:", user_instance.password)
                user_instance.set_password(confirm_psw)
                # print("After setting password:", user_instance.password)
                user_instance.save()

                messages.success(request, "Password Reset Successfully....")
                
                return redirect("login")
            except Exception as e:
                

                messages.error(request, f"An error occurred: {e}")

        else:
            messages.error(request, "Password Not Match")

    return render(request, "Authentication/reset_psw.html")


def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")

def Error404(request, exception):
    return render(request,'404.html')
    
    


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    

class FrontWebsite(ModelViewSet):
    queryset = FrontWebsiteEnquiry.objects.all()
    serializer_class = FrontWebsiteSerializer

    

 
def chats(request):
    user = request.user
    user_type = user.user_type

    if user_type == "2":
        chat_groups = ChatGroup.objects.all()
    else:
        chat_groups = user.chat_member.all()

    if user_type == "2":
        base_template = "dashboard/base.html"
    elif user_type == "3":
        base_template = "Employee/Base/base.html"
    else:
        base_template = "Agent/Base/base.html"

    context = {
        "groups": chat_groups,
        "base_template": base_template,
    }

    return render(request, "chat/chat.html", context)




from django.template import loader


# @login_required
def get_group_chat_messages(request):
    group_id = request.GET.get("group_id")
    # data = "data:application/pdf;base64,..."
    user = request.user

    # Retrieve chat messages for the selected group
    chat_group = ChatGroup.objects.get(id=group_id)
    chat = ChatMessage.objects.filter(group=chat_group)

    # messages = chat_group.messages.all()  # Assuming you have a related messages field

    context = {
        # "messages": messages,
        "chat_group": chat_group,
        "chat": chat,
        "user": user,
    }

    chat_content = loader.render_to_string("chat/group_chat_content.html", context)
    return HttpResponse(chat_content)

