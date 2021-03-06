from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.core.mail import send_mail
from crypto import settings
from django.template.loader import render_to_string
import random, requests, os
from .models import user

sms_text = lambda code : f'arztwitter verification code: {code}'
sms_signature = os.getenv('sms_signature')


def login(req):
    if req.method == 'GET':
        return render(req, 'login.html', {'next': req.GET.get('next') if req.GET.get('next') else ''})
    username = req.POST.get('username')
    password = req.POST.get('password')
    next_page = req.POST.get('next') if req.POST.get('next') else 'home'
    #check username
    User = auth.authenticate(username=username, password=password)
    if User:
        auth.login(req, User)
        return redirect(next_page)
    #check phone
    User = user.objects.filter(phone=username)
    if User and User[0].check_password(password) and User[0].verified_phone:
        auth.login(req, User[0])
        return redirect(next_page)
    #else return error
    return render(req, 'login.html', {'error':'کاربری با این اطلاعات وجود ندارد'})
    
def logout(req):
    auth.logout(req)
    return redirect('home')

def register(req, invite_code=''):
    if req.method == 'GET':
        return render(req, 'register.html', {'submit':'info', 'invite_code':invite_code, 'tab':'register'})
    else:
        data = {'username':req.POST.get('username'), 'phone':req.POST.get('phone'), 'password':req.POST.get('password'), 'cnf_password':req.POST.get('cnf_password'), 'name':req.POST.get('name'), 'invite_code':req.POST.get('invite_code')}
        #check username
        User = user.objects.filter(username=data.get('username'))
        if User:
            if User[0].verified_phone:
                data.update({'submit':'info', 'error':'این نام کاربری قبلا ثبت شده است'})
                return render(req, 'register.html', data)
            else:
                User[0].delete()
        #check password confirm
        if data.get('password') != data.get('cnf_password'):
            data.update({'submit':'info', 'error':'رمز عبور با تکرار آن همخوانی ندارد!'})
            return render(req, 'register.html', data)
        #check invite code
        if data.get('invite_code'):
            introducer = user.objects.filter(invite_code=data.get('invite_code'))
            if not introducer:
                introducer = None
                data.update({'submit':'info', 'error':'کد معرف صحیح نمی باشد!'})
                return render(req, 'register.html', data)
            introducer = introducer[0]
        else:
            introducer = None
        #check phone number
        User = user.objects.filter(phone=data.get('phone'))
        if User:
            if User[0].verified_phone:
                data.update({'submit':'info', 'error':'این شماره تلفن قبلا ثبت شده است!'})
                return render(req, 'register.html', data)
            else:
                User = User[0]
                User.username = data.get('username')
                User.set_password(data.get('password'))
                User.name = data.get('name').encode()
                User.introducer = introducer
                User.save()
        #create new user
        if not User:
            User = user.objects.create_user(data.get('username'), data.get('phone'), data.get('password'), data.get('name').encode(), introducer)
        #create and send verification code
        User.verify_code = random.randint(10000, 99999)
        User.verify_code_time = timezone.now()
        User.save()
        try:
            requests.get(f'http://sms.parsgreen.ir/UrlService/sendSMS.ashx?from=10001398&to={User.phone}&&text={sms_text(User.verify_code)}&signature={sms_signature}')
            return render(req, 'verify.html', {'phone':User.phone, 'seconds':119})
        except:
            data.update({'error':'شماره تلفن نادرست است!'})
            return render(req, 'register.html', data)


def verify_code(req):
    User = user.objects.get(phone=req.POST.get('phone'))
    #check verification code
    if (timezone.now()-User.verify_code_time).total_seconds()>120:
        return render(req, 'verify.html', {'phone': User.phone, 'error': 'زمان وارد کردن کد تایید بیش از حد مجاز', 'seconds':0})
    if req.POST.get('verification_code') != str(User.verify_code):
        return render(req, 'verify.html', {'phone': User.phone, 'error': 'کد تایید اشتباه است', 'seconds':int(119-(timezone.now()-User.verify_code_time).total_seconds())})
    User.verified_phone = True
    User.save()
    auth.login(req, User) 
    return redirect('home')
    


def resend_phone_code(req):
    User = user.objects.get(phone=req.GET.get('phone'))
    User.verify_code = random.randint(10000, 99999)
    User.verify_code_time = timezone.now()
    User.save()
    try:
        text = f'arztwitter verification code: {User.verify_code}'
        requests.get(f'http://sms.parsgreen.ir/UrlService/sendSMS.ashx?from=10001398&to={User.phone}&&text={text}&signature=0DBAC16D-54EA-4A7F-B200-4D5246409AAB')
        return render(req, 'verify.html', {'phone': User.phone, 'seconds':119})
    except:
        return JsonResponse({'status':'failed'})



@login_required(login_url='login')
def dashboard(req):
    return render(req, 'panel-dashboard.html')

@login_required(login_url='login')
def change_pass(req):
    if req.method == 'GET':
        return render(req, 'panel-change-password.html')
    if not req.user.check_password(req.POST.get('old_pass')):
        return render(req, 'panel-change-password.html', {'error':'رمز عبور فعلی اشتباه است'})
    if req.POST['new_pass'] != req.POST['cnf_new_pass']:
        return render(req, 'panel-change-password.html', {'error':'رمز عبور جدید با تکرار آن مطابق نیست'})
    req.user.set_password(req.POST['new_pass'])
    req.user.save()
    auth.login(req, req.user)
    return render(req, 'panel-change-password.html', {'message': 'رمز عبور با موفقیت تغییر کرد'})

@login_required(login_url='login')
def edit_profile(req):
    if req.method == 'GET':
        message = render_to_string('emails/email_verification.html', {'baseurl':settings.BASE_URL, 'username':req.user.username, 'session':req.user.get_session_auth_hash()})
        print(message)
        send_mail(
        subject='verify',
        message='',
        html_message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=['mr.mirshamsi.78@gmail.com']
    )
        return render(req, 'panel-edit-profile.html')


def verify_email(req):
    try:
        User = user.objects.get(username=req.GET.get('username'))
        if User.get_session_auth_hash() == req.GET.get('session'):
            User.verified_email = True
            User.save()
        return redirect('home')
    except:
        return redirect('home')
        

@login_required(login_url='login')
def invite_friends(req):
    return render(req, 'panel-invite-friends.html')
            

def validate_username(req):
    User = user.objects.filter(username=req.GET.get('username'))
    status = 'available'
    if User and User[0].verified_phone:
        status = 'not-available'
    return JsonResponse({'status':status})

def validate_phone(req):
    User = user.objects.filter(phone=req.GET.get('phone'))
    status = 'available'
    if User and User[0].verified_phone:
        status = 'not-available'
    return JsonResponse({'status':status})

def validate_email(req):
    User = user.objects.filter(email=req.GET.get('email'))
    status = 'available'
    if User and User[0].verified_email:
        status = 'not-available'
    return JsonResponse({'status':status})

def validate_invite_code(req):
    User = user.objects.filter(invite_code=req.GET.get('invite_code'))
    status = 'not-available'
    if User and User[0].verified_phone:
        status = 'available'
    return JsonResponse({'status':status})