from django.shortcuts import render
from django.http import HttpResponseRedirect
from django import forms
from django.utils.safestring import mark_safe
import QueryForm
from django import forms

from subprocess import call
from subprocess import Popen
from subprocess import PIPE
import download
import rank
import extract_terms
import os
import sys
import shutil
from collections import OrderedDict
import operator
from os import listdir
from os.path import isfile, join, exists

def populate_urls(request):
    fields = {}
    CHOICES = ((1,'Yes'),(2,'No'))
    if 'choice_urls_field1' not in request.session.keys() or 'search' in request.POST:
        # Display search results
        urlspath = '/Users/krishnam/Memex/memex/seed_crawler/seeds_generator/html'
        urls = [ download.decode(f) for f in listdir(urlspath) if isfile(join(urlspath,f)) ]
        index = 0
        for url in urls:
            request.session['choice_urls_field'+str(index)] = url
            fields['choice_urls_field'+str(index)] = forms.TypedChoiceField(label=mark_safe('<a href="'+url+'"target="_blank">'+url+'</a>'),required=False,widget=forms.RadioSelect(), choices=CHOICES,coerce=int)
            index = index + 1
    else:
        for key in request.session.keys():
            if 'choice_urls_field' in key:
                fields[key] = forms.TypedChoiceField(label=mark_safe('<a href="'+ request.session[key]+'"target="_blank">'+request.session[key]+'</a>'),required=False,widget=forms.RadioSelect(), choices=CHOICES,coerce=int)
                
    fields = OrderedDict(sorted(fields.items(), key=operator.itemgetter(0)))
            
    return type('QueryFormWithUrl', (forms.BaseForm,), { 'base_fields': fields })

def populate_freq_terms(request, terms):
    CHOICES = ((1,'Yes'),(2,'No'))
    fields = {}
    if len(terms) > 0:
        index = 0
        for term in terms:
            fields['choice_freq_terms_field'+str(index)] = forms.TypedChoiceField(label=mark_safe(term.title()),required=False,widget=forms.RadioSelect(), choices=CHOICES,coerce=int)
            request.session['choice_freq_terms_field'+str(index)] = term.title()
            index = index + 1
    else:
        for key in request.session.keys():
            if 'choice_freq_terms_field' in key:
                fields[key] = forms.TypedChoiceField(label=mark_safe(request.session[key]),required=False,widget=forms.RadioSelect(), choices=CHOICES,coerce=int)
    print "FREQ TERMS ",fields
    fields = OrderedDict(sorted(fields.items(), key=operator.itemgetter(0)))
    print "FREQ TERMS ORDERED",fields
    return type('QueryFormWithTerms', (forms.BaseForm,), { 'base_fields': fields })

def populate_ranked_terms(request,terms):
    CHOICES = ((1,'Yes'),(2,'No'))
    fields = {}
    if len(terms) > 0:
        index = 0
        for term in terms:
            fields['choice_ranked_terms_field'+str(index)] = forms.TypedChoiceField(label=mark_safe(term.title()),required=False,widget=forms.RadioSelect(), choices=CHOICES,coerce=int)
            request.session['choice_ranked_terms_field'+str(index)] = term.title()
            index = index + 1
    else:
        for key in request.session.keys():
            if 'choice_ranked_terms_field' in key:
                fields[key] = forms.TypedChoiceField(label=mark_safe(request.session[key]),required=False,widget=forms.RadioSelect(), choices=CHOICES,coerce=int)

    fields = OrderedDict(sorted(fields.items(), key=operator.itemgetter(0)))
    return type('QueryFormWithRankedTerms', (forms.BaseForm,), { 'base_fields': fields })

def add_to_search_freq(request):
    form_class = populate_freq_terms(request, [])
    form4 = form_class(request.POST)   
    int_yes_choices = []
    if form4.is_valid():
        for field in form4.cleaned_data:
            if "choice_freq_terms_field" in field:
                if form4.cleaned_data[field] == 1:
                    int_yes_choices.append(form4[field].label.lower().strip())
        
    return int_yes_choices

def add_to_search_rank(request):
    form_class = populate_ranked_terms(request, [])
    form5 = form_class(request.POST)   
    int_yes_choices = []
    if form5.is_valid():
        for field in form5.cleaned_data:
            if "choice_ranked_terms_field" in field:
                if form5.cleaned_data[field] == 1:
                    int_yes_choices.append(form5[field].label.lower().strip())
        
    return int_yes_choices
                
def populate_score(ranked_urls, scores):
    fields = {}
    urls = ""
    for i in range(0,len(ranked_urls)):
        urls = urls + "<br />"+ranked_urls[i]+" "+str(scores[i])
    fields["ranked_urls"] = forms.CharField(label=mark_safe(urls),required=False) 

    return type('RankedUrls', (forms.BaseForm,), { 'base_fields': fields })

def copy_files(int_yes_choices,int_no_choices):
    urlspath = '/Users/krishnam/Memex/memex/seed_crawler/seeds_generator/html/'
    classifier_data_positive_path = '/Users/krishnam/Memex/memex/pageclassifier/conf/sample_training_data/positive'
    classifier_data_negative_path = '/Users/krishnam/Memex/memex/pageclassifier/conf/sample_training_data/negative'
    files = [ f for f in listdir(urlspath) if isfile(join(urlspath,f))]
    [ shutil.copy(urlspath+files[index], classifier_data_positive_path) for index in int_yes_choices ]
    [ shutil.copy(urlspath+files[index], classifier_data_negative_path) for index in int_no_choices ]
        
    
def get_query(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        form1 = QueryForm.QueryForm(request.POST)
        if 'search' in request.POST:
            # create a form instance and populate it with data from the request:
            # check whether it's valid:
            if form1.is_valid():
                # Search Bing for the urls related to the query terms
                query_terms = form1.cleaned_data['query_terms']
                
                os.chdir('/Users/krishnam/Memex/memex/seed_crawler/seeds_generator')
                
                with open('conf/queries.txt','w') as f:
                    f.write(query_terms)
                    
                p=Popen("java -cp .:class:libs/commons-codec-1.9.jar BingSearch -t 15",shell=True,stdout=PIPE)
                output, errors = p.communicate()
                print output
                print errors
                call(["rm", "-rf", "html"])
                call(["mkdir", "-p", "html"])
                dl = download.download("results.txt","html")
                
                if exists("/Users/krishnam/Memex/memex/seed_crawler/ranking/exclude.txt"):
                    call(["rm", "/Users/krishnam/Memex/memex/seed_crawler/ranking/exclude.txt"])

                form_class = populate_urls(request)
                form2 = form_class()
                print "Sessions ", request.session.keys()
                # redirect to a new URL:
                return render(request, 'query_with_results.html', {'form1': form1,'form2':form2})

        form_class = populate_urls(request)
        form2 = form_class(request.POST)
        int_url_yes_choices = []
        int_url_no_choices = []
        if form2.is_valid():
            # If relevant pages are selected do the ranking
            for field in form2.cleaned_data:
                if form2.cleaned_data[field] == 1:
                    int_url_yes_choices.append(int(field.replace("choice_urls_field","")))
                elif form2.cleaned_data[field] == 2:
                    int_url_no_choices.append(int(field.replace("choice_urls_field","")))

        if 'rank' in request.POST:
                        
                copy_files(int_url_yes_choices,int_url_no_choices)
                        
                os.chdir('/Users/krishnam/Memex/memex/seed_crawler/lda_pipeline')
                call(["mkdir", "-p", "data"])
                p=Popen("java -cp .:class/:lib/boilerpipe-1.2.0.jar:lib/nekohtml-1.9.13.jar:lib/xerces-2.9.1.jar Extract ../seeds_generator/html/  | python concat_nltk.py data/lda_input.csv",shell=True,stdout=PIPE)
                output, errors = p.communicate()
                print output
                print errors
                
                os.chdir('/Users/krishnam/Memex/memex/seed_crawler/ranking')
                ranker = rank.rank()
                [ranked_urls,scores] = ranker.results('/Users/krishnam/Memex/memex/seed_crawler/lda_pipeline/data/lda_input.csv',int_url_yes_choices, int_url_no_choices)
                print "Scores ", scores
                form_class = populate_score(ranked_urls, scores)
                form3 = form_class()
                return render(request, 'query_with_ranks.html', {'form1': form1,'form2':form2, 'form3':form3})

        elif 'extract' in request.POST:
            os.chdir('/Users/krishnam/Memex/memex/seed_crawler/ranking')
            if exists("selected_terms.txt"):
                call(["rm", "selected_terms.txt"])
            if exists("exclude.txt"):
                call(["rm", "exclude.txt"])
            extract = extract_terms.extract_terms('/Users/krishnam/Memex/memex/seed_crawler/lda_pipeline/data/lda_input.csv',int_url_no_choices)
            form_class = populate_freq_terms(request, extract.getTopTerms(20))
            form4 = form_class()
            return render(request, 'query_with_terms.html', {'form1': form1,'form2':form2, 'form4':form4})
                
        elif ('rank_terms' in request.POST):
            form_class = populate_freq_terms(request,[])
            form4 = form_class(request.POST)
            if form4.is_valid():
                int_yes_choices = []
                int_no_choices = []
                for field in form4.cleaned_data:
                    if "choice_freq_terms_field" in field:
                        if form4.cleaned_data[field] == 1:
                            #int_yes_choices.append(int(field.replace("choice_freq_terms_field","")))
                            int_yes_choices.append(form4[field].label.lower().strip())
                        elif form4.cleaned_data[field] == 2:
                            #int_no_choices.append(int(field.replace("choice_freq_terms_field","")))
                            int_no_choices.append(form4[field].label.lower().strip())
                            
                os.chdir('/Users/krishnam/Memex/memex/seed_crawler/ranking')
                with open('exclude.txt','w+') as f:
                    for choice in int_no_choices :
                        print "Choice Not in Words ", choice
                        f.write(choice+'\n')

                extract = extract_terms.extract_terms('/Users/krishnam/Memex/memex/seed_crawler/lda_pipeline/data/lda_input.csv', int_url_no_choices)
                [ranked_terms,scores] = extract.results(int_yes_choices)
                form_class = populate_ranked_terms(request, ranked_terms[0:20])
                form5 = form_class()

                with open('selected_terms.txt','w+') as f:
                    for choice in int_yes_choices :
                        f.write(choice+'\n')

                return render(request, 'query_with_term_rank.html', {'form1': form1,'form2':form2, 'form4':form4, 'form5':form5})
                
        elif 'rank_terms_1' in request.POST:
            form_class = populate_freq_terms(request,[])
            form4 = form_class(request.POST)

            form_class = populate_ranked_terms(request,[])
            form5 = form_class(request.POST)
            if form5.is_valid():
                int_yes_choices = []
                int_no_choices = []
                
                for field in form5.cleaned_data:
                    if "choice_ranked_terms_field" in field:
                        if form5.cleaned_data[field] == 1:
                            #int_yes_choices.append(int(field.replace("choice_ranked_terms_field","")))
                            int_yes_choices.append(form5[field].label.lower().strip())
                        elif form5.cleaned_data[field] == 2:
                            #int_no_choices.append(int(field.replace("choice_ranked_terms_field","")))
                            int_no_choices.append(form5[field].label.lower().strip())

                os.chdir('/Users/krishnam/Memex/memex/seed_crawler/ranking')
                past_yes_terms = []
                if exists("selected_terms.txt"):
                    with open('selected_terms.txt','r') as f:
                        past_yes_terms = [line.strip() for line in f.readlines()]

                with open('selected_terms.txt','w+') as f:
                    for word in past_yes_terms:
                        f.write(word+'\n')
                    for choice in int_yes_choices :
                        if choice not in past_yes_terms:
                            f.write(choice+'\n')

                past_no_terms = []
                if exists("exclude.txt"):
                    with open('exclude.txt','r') as f:
                        past_no_terms = [line.strip() for line in f.readlines()]

                with open('exclude.txt','w+') as f:
                    for word in past_no_terms:
                        f.write(word+'\n')
                    for choice in int_no_choices :
                        if choice not in past_no_terms:
                            f.write(choice+'\n')

                extract = extract_terms.extract_terms('/Users/krishnam/Memex/memex/seed_crawler/lda_pipeline/data/lda_input.csv', int_url_no_choices)
                   
                [ranked_terms,scores] = extract.results(int_yes_choices+past_yes_terms)
                form_class = populate_ranked_terms(request, ranked_terms[0:20])
                form5 = form_class(request.POST)                

                return render(request, 'query_with_term_rank.html', {'form1': form1,'form2':form2, 'form4':form4, 'form5':form5})

        elif 'add_to_search_freq' in request.POST:
            form_class = populate_freq_terms(request,[])
            form4 = form_class(request.POST)

            results = add_to_search_freq(request)
            form1 = QueryForm.QueryForm(request.POST)
            if form1.is_valid():
                query_terms = form1.cleaned_data['query_terms']
                print query_terms
                for word in results:
                    query_terms = query_terms + " " + word;
                form1 = QueryForm.QueryForm(initial={'query_terms':query_terms})
                return render(request, 'query_with_terms.html', {'form1': form1,'form2':form2, 'form4':form4})

        elif 'add_to_search_rank' in request.POST:
            form_class = populate_freq_terms(request,[])
            form4 = form_class(request.POST)
            form_class = populate_ranked_terms(request, [])
            form5 = form_class(request.POST)                

            results = add_to_search_rank(request)
            form1 = QueryForm.QueryForm(request.POST)
            if form1.is_valid():
                query_terms = form1.cleaned_data['query_terms']
                print query_terms
                for word in results:
                    query_terms = query_terms + " " + word;
                form1 = QueryForm.QueryForm(initial={'query_terms':query_terms})
                return render(request, 'query_with_term_rank.html', {'form1': form1,'form2':form2, 'form4':form4, 'form5':form5})

    # if a GET (or any other method) we'll create a blank form
    else:
        form1 = QueryForm.QueryForm()
        
    return render(request, 'query.html', {'form1': form1})


    