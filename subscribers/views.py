from django.shortcuts import render
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect

from django.contrib.auth import authenticate, login
from django.forms.forms import NON_FIELD_ERRORS
from django.conf import settings
from django.core.urlresolvers import reverse

from .forms import SubscriberForm
from .models import Subscriber

import stripe

def subscriber_new(request, template='subscribers/subscriber_new.html'):
    if request.method == 'POST':
        form = SubscriberForm(request.POST)
        if form.is_valid():

            # Unpack form values
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']

            # Create the User record
            user = User(username=username, email=email)
            user.set_password(password)
            # user.save()
            try:
                user.save()
            except Exception as e:
                form._errors['username'] = form.error_class(['This username is already taken!'])
                return render(request, template,
                    {'form':form,
                     'STRIPE_PUBLISHABLE_KEY':settings.STRIPE_PUBLISHABLE_KEY}
                )

            # Create Subscriber Record
            address_one = form.cleaned_data['address_one']
            address_two = form.cleaned_data['address_two']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            sub = Subscriber(address_one=address_one, address_two=address_two,
                city=city, state=state, user_rec=user)
            sub.save()

            # Process payment (via Stripe)
            if request.POST.get("signup-only"):
                fee = settings.SUBSCRIPTION_PRICE
                try:
                    stripe_customer = sub.charge(request, email, fee)
                except stripe.StripeError as e:
                    form._errors[NON_FIELD_ERRORS] = form.error_class([e.args[0]])
                    return render(request, template,
                        {'form':form,
                         'STRIPE_PUBLISHABLE_KEY':settings.STRIPE_PUBLISHABLE_KEY}
                    )
            
            # Auto login the user
            a_u = authenticate(username=username, password=password)
            if a_u is not None:
                if a_u.is_active:
                    login(request, a_u)
                    return HttpResponseRedirect(reverse('account_list'))
                else:
                    return HttpResponseRedirect(
                        reverse('django.contrib.auth.views.login')
                    )
            else:
                return HttpResponseRedirect(reverse('sub_new'))
    else:
        form = SubscriberForm()

    return render(request, template,
    {'form':form,
     'STRIPE_PUBLISHABLE_KEY':settings.STRIPE_PUBLISHABLE_KEY})