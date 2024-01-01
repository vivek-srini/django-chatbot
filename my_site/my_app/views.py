

# Create your views here.

# myapp/views.py
from django.shortcuts import render
from .forms import KeywordForm,TradeExclusionForm
import tempfile
import boto3
import json
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.http import JsonResponse
import pandas as pd
from datetime import datetime
from langchain.embeddings import OpenAIEmbeddings
import openai
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from .forms import SignUpForm
from .forms import ChatBotForm
from .models import user_pass
from .forms import LogInForm,LogOutForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User


openai_api_key = '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'


chat_history = {"question":[],"answer":[]}



embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

def update_cost(user_query, response,use_instant=False):
    df = pd.read_excel("my_app/account_keeper.xlsx")
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    today_date_only = datetime.now().date()
    current_inp_tokens = int(len(user_query)/6)
    current_out_tokens = int(len(response)/6)
    if use_instant==False:
      current_cost = (current_inp_tokens*0.008)/1000 + (current_out_tokens*0.024)/1000
    else:
      current_cost = (current_inp_tokens*0.00163)/1000 + (current_out_tokens*0.00551)/1000
    print(current_cost)
    # Check if there is any row with today's date
    if (df['Date'] == today_date_only).any():
        # Get the current cost for today (if available)
        cost_today = df.loc[df['Date'] == today_date_only, 'Cost'].iloc[0]
        # Calculate the total cost
        total_cost = current_cost + cost_today
        # Update the cost for today's date
        df.loc[df['Date'] == today_date_only, 'Cost'] = total_cost
    else:
        # Handle case where today's date is not in the DataFrame
        # You can append a new row or handle as needed
        pass

    # Save the updated DataFrame back to the Excel file
    df.to_excel("my_app/account_keeper.xlsx")



def langchain_response_without_prompt(db, question, chatbot_style):
    global chat_history
    question = chatbot_style + f"""Question: {question}"""
    openai = OpenAI(
    api_key="OGBvBYDAo3k0jpYfXq0A1V1XORW4Cjqg",
    base_url="https://api.deepinfra.com/v1/openai",
)

    chat_completion = openai.chat.completions.create(
    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
    messages=[{"role": "user", "content": f"{question}"}]
)
    chat_history["question"].append(question)
    chat_history["answer"].append(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content


def create_db(file_path):
    with open(file_path) as file:
        text = file.read()
    text_splitter = RecursiveCharacterTextSplitter(
        
        chunk_size=2000,
        chunk_overlap=0
        
      )
    chunks = text_splitter.split_text(text)


    

    db = FAISS.from_texts(chunks, embeddings)
    return db


# Create db outside of the view function
db = None
login_required
def keyword_view(request):
    global db  # Reference the global db variable
   
   
    preferred_style = request.session.get('preferred_style', 'default_style')
    print(preferred_style)
    if preferred_style == "Friendly":
        chatbot_style = "You are a happy and friendly chatbot. Please answer the questions in a very friendly and chatty,happy way."
    elif preferred_style == "Rude":
        chatbot_style = "You are a rude and angry chatbot. Please answer the questions in a very rude and angry way."
    elif preferred_style == "Tired":
        chatbot_style = "You are a tired and sleepy chatbot. Please answer the questions in a very tired and sleepy way."
    else:
        chatbot_style = "You are a happy and friendly chatbot. Please answer the questions in a very friendly and chatty,happy way."
          
    action = request.POST.get('action', '')
    if action == 'chat_response':
        user_query = request.POST.get('user_query', '')
        user_query = f"This is the Chat History so far:{str(chat_history)}" + "\n" + user_query 
        bot_response = langchain_response_without_prompt(db, user_query, chatbot_style)
        return HttpResponse(bot_response.replace("\n", "<br>"))  # Converting new lines for HTML

        # If it's not a POST request or no file is uploaded, render the form
    #return render(request, 'my_app/keyword_form.html')
    # else:
    #     return render(request, 'my_app/keyword_form.html', {'form': chatbot_form})

    # If it's not a POST request, render the form without the message
    print(preferred_style)
    if preferred_style=="Friendly":
        image_path = "happy_image.png"
    elif preferred_style=="Tired":
        image_path = "tired_image.png"
    elif preferred_style=="Rude":
        image_path = "rude_image.png"
    else:
        image_path = "happy_image.png"
    
    return render(request, 'my_app/keyword_form.html',context={"chatbot_style":preferred_style,"image_path":image_path})


def sign_up(request):
    error = False

    if request.method=="POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            if User.objects.filter(username=username).exists():
                error = True
                return render(request, 'my_app/sign_up.html', {'form': form, 'error_message': 'Username already exists.',"error":error})
            else:
                user = User.objects.create_user(username=username, password=password)
                login(request,user)
                return redirect('keyword_form')
           
            
            

            # Redirect to the login page
                #return render(request, 'my_app/sign_up.html', {'form': form, 'success_message': 'Sign up successful!',"error":error})
            

    else:
        form = SignUpForm()
        return render(request, 'my_app/sign_up.html', {'form': form})


def choose_chatbot(request):
    if request.method == "POST":
        form = ChatBotForm(request.POST)
        if form.is_valid():
            preferred_style = form.cleaned_data['preferred_style']
            request.session['preferred_style'] = preferred_style
            request.session.save()
            return redirect("keyword_form")
    else:
        form = ChatBotForm()
    return render(request, 'my_app/choose_chatbot.html', {'form': form})


def log_in(request):
    error = False
    if request.method=="POST":
        form = LogInForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('choose_chatbot_form')

            # Check if the username and password exist in the table
            # if user_pass.objects.filter(username=username, password=password).exists():
                
            #     return redirect('keyword_form')
            #     return render(request, 'my_app/log_in.html', {'form': form, 'success_message': 'Log in successful!',"error":error})
            else:
                error = True
                return render(request,'my_app/log_in.html',{"form":form,"error_message":"Username or password is incorrect.","error":error})
        else:
            # Handle the invalid form case
            return render(request, 'my_app/log_in.html', {'form': form, 'error_message': 'Form data is invalid.', "error": True})
            
    else:
        form = LogInForm()
        return render(request, 'my_app/log_in.html', {'form': form})

def log_out(request):
    if request.method=="POST":
        form = LogOutForm(request.POST)
        if form.is_valid():
            return redirect("login_form")
    else:
        form = LogOutForm()
        return render(request, 'my_app/keyword_form.html', {'form': form})
   