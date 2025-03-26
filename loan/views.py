from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from datetime import datetime
from UserApp.models import *
from django.http import JsonResponse
from UserApp.forms import *


def loanform(request):
    user_id = request.session.get('user_id', None)
    if user_id is None:
        return redirect('/login')

    user_type = request.session.get('user_type', None)

    # Check for Admin
    if user_type == 'admin':
        try:
            admin = AdminModel.objects.get(pk=user_id)
        except AdminModel.DoesNotExist:
            return redirect('/login')

        admin_name = f"{admin.admin_first_name} {admin.admin_last_name}" if admin.admin_last_name else f"{admin.admin_first_name}"

        if admin.is_superadmin:
            loan = LoanModel.objects.all()
        elif admin.is_staff:
            connected_franchises = Franchise.objects.filter(staff=admin)
            loan = LoanModel.objects.filter(franchise__in=connected_franchises)
        else:
            loan = LoanModel.objects.filter(franchise=admin)

    # Check for Staff
    elif user_type == 'staff':
        try:
            staff = StaffModel.objects.get(pk=user_id)
        except StaffModel.DoesNotExist:
            return redirect('/login')

        staff_name = f"{staff.first_name} {staff.last_name if staff.last_name else ''}"

        # Assuming staff can only see loans assigned to them or their franchise
        # connected_franchises = Franchise.objects.filter(staff=staff)
        loan = LoanModel.objects.all()

    else:
        return redirect('/login')

    status = StatusModel.objects.all()
    bank = BankModel.objects.all()

    if request.method == 'POST':
        files = request.FILES.getlist('files')
        form = LoanApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            loan_form = form.save(commit=False)

            # Only admins can assign a franchise if not superadmin or staff
            if user_type == 'admin' and not admin.is_superadmin and not admin.is_staff:
                loan_form.franchise = admin
            elif user_type == 'staff':
                loan_form.franchise = staff.franchise  # Assuming staff has a franchise

            loan_form.save()

            for file in files:
                UploadedFile.objects.create(
                    file=file,
                    loan_application=loan_form
                )

            return redirect('/')

    else:
        form = LoanApplicationForm()

    # If user is admin, show their name, else show staff name
    username = admin_name if user_type == 'admin' else staff_name

    return render(request, 'loan-form.html', {
        'username': username,
        'loan': loan,
        'status': status,
        'bank': bank,
        'form': form
    })



def loan_page(request, form_id):
    user_id = request.session.get('user_id', None)
    if user_id is None:
        return redirect('/login')

    admin = AdminModel.objects.get(admin_id=user_id)

    # Allow both superadmins and staff to access all loans
    if admin.is_superadmin or admin.is_staff:
        pass
    else:
        # Regular admins should only access loans from their assigned franchise
        if form_instance.franchise != admin:
            return redirect('/')

    admin_name = f"{admin.admin_first_name} {admin.admin_last_name}" if admin.admin_last_name else f"{admin.admin_first_name}"
    form_instance = get_object_or_404(LoanApplicationModel, form_id=form_id)
    files = UploadedFile.objects.filter(loan_application=form_instance)

    if request.method == 'POST':
        form = LoanApplicationForm(request.POST, instance=form_instance)

        if request.POST.get('submit-form'):
            # Give same edit permissions to both superadmin and staff
            form_instance.first_name = request.POST.get('first_name', form_instance.first_name)
            form_instance.last_name = request.POST.get('last_name', form_instance.last_name)
            form_instance.district = request.POST.get('district', form_instance.district)
            form_instance.place = request.POST.get('place', form_instance.place)
            form_instance.phone_no = request.POST.get('phone_no', form_instance.phone_no)

            loan_id = request.POST.get('loan_name')
            if loan_id:
                form_instance.loan_name = LoanModel.objects.get(loan_id=loan_id)

            form_instance.loan_amount = request.POST.get('loan_amount', form_instance.loan_amount)

            bank_id = request.POST.get('bank_name')
            if bank_id:
                form_instance.bank_name = BankModel.objects.get(bank_id=bank_id)

            form_instance.executive_name = request.POST.get('executive_name', form_instance.executive_name)
            form_instance.mobileno_1 = request.POST.get('mobileno_1', form_instance.mobileno_1)
            form_instance.mobileno_2 = request.POST.get('mobileno_2', form_instance.mobileno_2)
            form_instance.followup_date = request.POST.get('followup_date', form_instance.followup_date)
            form_instance.description = request.POST.get('description', form_instance.description)

            status_id = request.POST.get('status_name')
            if status_id:
                form_instance.status_name = StatusModel.objects.get(status_id=status_id)

            form_instance.application_description = request.POST.get('application_description', form_instance.application_description)
            form_instance.save()
            
            return redirect('/')

        if request.POST.get('new_files'):
            files = request.FILES.getlist('uploaded_files')
            for file in files:
                UploadedFile.objects.create(
                    file=file,
                    loan_application=form_instance
                )
            return redirect('loan-page', form_id)

    else:
        form = LoanApplicationForm(instance=form_instance)

    return render(request, 'loan-page.html', {
        'username': admin_name,
        'admin': admin,
        'form': form,
        'files': files
    })




def all_app(request):
    user_id = request.session.get('user_id', None)
    if user_id is None:
        return redirect('/login')  # Redirect to login if no user_id in session

    user_type = request.session.get('user_type', None)

    # Handle Admin and Staff User
    if user_type in ['admin', 'staff']:
        try:
            # For admin user
            if user_type == 'admin':
                admin = AdminModel.objects.get(admin_id=user_id)
                admin_name = f"{admin.admin_first_name} {admin.admin_last_name}" if admin.admin_last_name else f"{admin.admin_first_name}"

            # For staff user
            else:
                staff = StaffModel.objects.get(staff_id=user_id)
                staff_name = f"{staff.first_name} {staff.last_name if staff.last_name else ''}"

        except (AdminModel.DoesNotExist, StaffModel.DoesNotExist):
            return redirect('/login')  # Redirect if user does not exist

        # Retrieve all loan applications for both admin and staff
        loan_app = LoanApplicationModel.objects.all()

    # Handle Franchise User
    elif user_type == 'franchise':
        try:
            franchise = Franchise.objects.get(id=user_id)
            franchise_name = franchise.name
        except Franchise.DoesNotExist:
            return redirect('/login')  # Redirect if franchise does not exist

        # Get loan applications specific to the franchise
        loan_app = LoanApplicationModel.objects.filter(franchise=franchise)
        franchise_name = franchise.name

    else:
        return redirect('/login')

    # Filtering by loan name (if provided)
    loan_name_filter = request.GET.get('loan_name', '')
    if loan_name_filter:
        loan_app = loan_app.filter(loan_name__icontains=loan_name_filter)

    # Render the response with the loan applications
    return render(request, 'all-files.html', {
        'username': admin_name if user_type == 'admin' else staff_name if user_type == 'staff' else franchise_name,
        'loan_applications': loan_app,  # Show the loan applications
        'loan_name_filter': loan_name_filter  # Pass the current loan name filter back to the template
    })




def loan_application_status(request):
    user_phone = request.GET.get('phone_no')
    loan_application = get_object_or_404(
        LoanApplicationModel, phone_no=user_phone)
    status = loan_application.status_name.status_name if loan_application.status_name else "Not Available"

    def get_progress_percentage(status):
        return {
            "Application Started": 33,
            "Pending": 66,
            "Completed": 100,
        }.get(status, 0)

    context = {
        'progress_percentage': get_progress_percentage(status),
        'status': status,
    }
    return render(request, 'dashboard.html', context)


def update_status(request, form_id):
    loan_form = get_object_or_404(LoanApplicationModel, form_id=form_id)
    user_id = request.session.get('user_id', None)
    if user_id is None:
        return redirect('/login')

    admin = AdminModel.objects.get(admin_id=user_id)

    if not admin.is_superadmin and not admin.is_staff:
        return redirect('/')

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['Accept', 'Reject']:
            loan_form.workstatus = status
            loan_form.save()
    return redirect('/')


def addloan(request):
    user_id = request.session.get('user_id')
    user_type = request.session.get('user_type')

    if not user_id or user_type not in ['admin', 'staff', 'franchise']:
        return JsonResponse({"error": "Unauthorized access"}, status=403)

    # Handle Admin user
    if user_type == 'admin':
        try:
            admin = AdminModel.objects.get(admin_id=user_id)
        except AdminModel.DoesNotExist:
            return JsonResponse({"error": "Admin not found"}, status=403)

        admin_name = f"{admin.admin_first_name} {admin.admin_last_name}" if admin.admin_last_name else admin.admin_first_name

    # Handle Staff user
    elif user_type == 'staff':
        try:
            staff = StaffModel.objects.get(staff_id=user_id)
        except StaffModel.DoesNotExist:
            return JsonResponse({"error": "Staff not found"}, status=403)

        admin_name = f"{staff.first_name} {staff.last_name if staff.last_name else ''}"
    
    # Handle the form submission
    if request.method == 'POST':
        form = LoanForm(request.POST)
        if form.is_valid():
            loan = form.save()
            return JsonResponse({
                "success": True,
                "loan_id": loan.loan_id,
                "loan_name": loan.loan_name
            })

        return JsonResponse({"error": form.errors}, status=400)

    all_loans = LoanModel.objects.all()
    form = LoanForm()

    return render(request, 'add-loan.html', {
        'username': admin_name,
        'form': form,
        'all_loans': all_loans
    })


# Handle add status
def addstatus(request):
    user_id = request.session.get('user_id', None)
    user_type = request.session.get('user_type', None)

    if not user_id or user_type not in ['admin', 'staff']:
        return redirect('/login')

    # Handle Admin user
    if user_type == 'admin':
        try:
            admin = AdminModel.objects.get(admin_id=user_id)
        except AdminModel.DoesNotExist:
            return redirect('/login')  # Redirect if Admin not found

        admin_name = f"{admin.admin_first_name} {admin.admin_last_name}" if admin.admin_last_name else admin.admin_first_name
    # Handle Staff user
    elif user_type == 'staff':
        try:
            staff = StaffModel.objects.get(staff_id=user_id)
        except StaffModel.DoesNotExist:
            return redirect('/login')  # Redirect if Staff not found

        admin_name = f"{staff.first_name} {staff.last_name if staff.last_name else ''}"

    all_status = StatusModel.objects.all()
    
    if request.method == 'POST':
        form = StatusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = StatusForm()

    return render(request, 'add-status.html', {
        'username': admin_name,
        'form': form,
        'all_status': all_status
    })


# Handle add bank
def addbank(request):
    user_id = request.session.get('user_id', None)
    user_type = request.session.get('user_type', None)
    
    if not user_id or user_type not in ['admin', 'staff']:
        return redirect('/login')
    
    # Handle Admin user
    if user_type == 'admin':
        try:
            admin = AdminModel.objects.get(admin_id=user_id)
        except AdminModel.DoesNotExist:
            return redirect('/login')  # Redirect if Admin not found
        
        admin_name = f"{admin.admin_first_name} {admin.admin_last_name}" if admin.admin_last_name else admin.admin_first_name
    
    # Handle Staff user
    elif user_type == 'staff':
        try:
            staff = StaffModel.objects.get(staff_id=user_id)
        except StaffModel.DoesNotExist:
            return redirect('/login')  # Redirect if Staff not found
        
        admin_name = f"{staff.first_name} {staff.last_name if staff.last_name else ''}"
    
    # Change allbank to all_bank to match the context variable
    allbank = BankModel.objects.all()
    
    if request.method == 'POST':
        form = BankForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bank added successfully!')
            return redirect('addbank')
    else:
        form = BankForm()
    
    return render(request, 'add-bank.html', {
        'username': admin_name,
        'form': form,
        'allbank': allbank
    })



def delete_loan(request, loan_id):
    user_id = request.session.get('user_id', None)
    if user_id is None:
        return redirect('/login')

    admin = AdminModel.objects.get(admin_id=user_id)

    loan = get_object_or_404(LoanModel, pk=loan_id)
    if not admin.is_superadmin and (loan.franchise != admin):
        return redirect('/')

    if request.method == 'POST':
        loan.delete()
        return redirect('addloan')
    return redirect('addloan')


def delete_status(request, status_id):
    user_id = request.session.get('user_id', None)
    if user_id is None:
        return redirect('/login')

    admin = AdminModel.objects.get(admin_id=user_id)

    if not admin.is_superadmin:
        return redirect('/')

    status = get_object_or_404(StatusModel, pk=status_id)
    if request.method == 'POST':
        status.delete()
        return redirect('addstatus')
    return redirect('addstatus')


def delete_bank(request, bank_id):
    user_id = request.session.get('user_id', None)
    if user_id is None:
        return redirect('/login')

    admin = AdminModel.objects.get(admin_id=user_id)

    if not admin.is_superadmin:
        return redirect('/')

    bank = get_object_or_404(BankModel, pk=bank_id)
    if request.method == 'POST':
        bank.delete()
        return redirect('addbank')
    return redirect('addbank')


def delete_loanpage(request, form_id):
    user_id = request.session.get('user_id', None)
    if user_id is None:
        return redirect('/login')

    admin = AdminModel.objects.get(admin_id=user_id)

    loan = get_object_or_404(LoanApplicationModel, pk=form_id)
    if not admin.is_superadmin and (loan.franchise != admin):
        return redirect('/')

    if request.method == 'POST':
        loan.delete()
        return redirect('/')
    return redirect('/')

def delete_files(request, id):
    file = get_object_or_404(UploadedFile, pk=id)
    loan_id = file.loan_application.form_id
    if request.method == 'POST':
        file.delete()
        return redirect('loan-page', loan_id)  # Adjust the redirect based on your URL name for the user list page
    return redirect('loan-page', loan_id)
