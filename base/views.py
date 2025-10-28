from django.shortcuts import render,redirect,get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import Room,Topic,Message,User,ContactUs
from django.contrib.auth.decorators import login_required

from .models import Room,Topic,Message
from .forms import RoomForm, UserForm


from django.http import Http404

def loginUser(request):
    
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'User does not exist')
                return render(request, 'login.html')
            
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Email or password is incorrect')
        else:
            messages.error(request, 'Both email and password are required')
    
    
    return render(request,'login.html')

def logoutUser(request):
    logout(request)
    return redirect('login')

def registerPage(request):
    if request.method=="POST":
        username=request.POST.get('username')
        password=request.POST.get('password')
        email=request.POST.get('email')
        if not username or not password or not email:
            messages.error(request, 'All fields are required')
            return render(request, 'register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'register.html')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'register.html')
        else:
            user=User.objects.create_user(username=username,email=email)
            user.set_password(password)
            user.save()
        return redirect('login')
    return render(request,'register.html')


def home(request):
    q=request.GET.get('q') if request.GET.get('q')!=None else ''
    rooms=Room.objects.filter(
        Q(topic__name__icontains=q ) or
        Q(name__icontains=q ) or
        Q(description__icontains=q)
        )
    room_count=rooms.count()
    room_messages=Message.objects.filter(Q(room__topic__name__icontains=q))
    topics=Topic.objects.all()
    context={'rooms':rooms,'topics':topics,
             'room_count':room_count,
             'room_messages':room_messages
             }
    return render(request,'home.html',context)

def room(request,pk):
    room=Room.objects.get(id=pk)
    room_messages=room.message_set.all().order_by('-created')
    participants=room.participants.all()

    if request.method=='POST':
        message=Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')

        )
        room.participants.add(request.user)
        return redirect('room',pk=room.id)
    context={'room':room,'room_messages':room_messages,'participants':participants}
    
    return render(request,'room.html',context)


def userProfile(request,pk):
    try:
        user = User.objects.get(id=pk)
    except User.DoesNotExist:
        raise Http404("User does not exist")
    rooms=user.room_set.all()
    room_messages=user.message_set.all()
    topics=Topic.objects.all()
    context={'user':user,'rooms':rooms,
             'room_messages':room_messages,'topics':topics}
    context={'rooms':rooms,'user':user}
    return render(request,'profile.html',context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        

        Room.objects.create(
            host=User.objects.get(pk=request.user.pk),
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
       
        return redirect('home')

    context = {'form': form, 'topics': topics}
    return render(request, 'room_form.html', context)

@login_required(login_url='login')
def updateRoom(request,pk):
    room=Room.objects.get(id=pk)
    form=RoomForm(instance=room)
    
    if request.user!=room.host:
        return HttpResponse("You are not allowed here")
    if request.method=='POST':
        form=RoomForm(request.POST,request.FILES,instance=room)
        if form.is_valid():
            form.save()
            return redirect('/')
    context={'form':form}
    return render(request,'room_form.html',context)


@login_required(login_url='login')
def deleteRoom(request,pk):
    room=Room.objects.get(id=pk)
    if request.user!=room.host:
        return HttpResponse("You are not allowed here")
    if request.method=='POST':
        room.delete()
        return redirect('/')
    return render(request,'delete.html',{'obj':room})

@login_required(login_url='login')

def deleteMessage(request,pk):
    message = get_object_or_404(Message, id=pk)
    
   
    if request.user != message.user:
        return HttpResponse("You are not allowed here")
    
    if request.method == 'POST':
        
        room = message.room
        message.delete()
        
        
        return redirect('/')

    return render(request, 'delete.html', {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, 'update-user.html', {'form': form})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'topics.html', {'topics': topics})


def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'activity.html', {'room_messages': room_messages})

def aboutPage(request):
    return render(request, 'about.html')

def contactPage(request):
    if request.method=="POST":
        name=request.POST.get('name')
        email=request.POST.get('email')
        message=request.POST.get('message')
        if not name or not email or not message:
            messages.error(request, 'All fields are required')
            return render(request, 'contact.html')
        else:
            contact_message=ContactUs.objects.create(name=name,email=email,message=message)
            contact_message.save()
            messages.success(request, 'We got your message and will get back to you shortly!')
            return redirect('contact')
    return render(request, 'contact.html')