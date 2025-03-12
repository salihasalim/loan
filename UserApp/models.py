from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now
import uuid
import random
import string


class AdminModel(models.Model):
    admin_id = models.AutoField(primary_key=True)
    admin_first_name = models.CharField(max_length=100)
    admin_last_name = models.CharField(max_length=100, blank=True, null=True)
    admin_email = models.EmailField(unique=True)
    admin_phone = models.CharField(
        max_length=10,
        validators=[RegexValidator(
            regex=r'^\d{10}$', message="Enter a valid 10-digit mobile number.")],
        null=True, blank=True
    )
    admin_password = models.CharField(max_length=128)
    is_superadmin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(
        auto_now_add=True)  # Manually set default here
    last_login = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.admin_password and not self.admin_password.startswith('pbkdf2_'):
            self.admin_password = make_password(self.admin_password)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.admin_first_name} {self.admin_last_name}"


class StaffModel(models.Model):
    staff_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_no = models.CharField(
        max_length=10,
        validators=[RegexValidator(
            regex=r'^\d{10}$', message="Enter a valid 10-digit mobile number.")]
    )
    password = models.CharField(max_length=128, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    profile_completed = models.BooleanField(default=False)  # To track if staff completed the profile
    adhaar_no = models.CharField(max_length=100, null=True, blank=True)
    adhaar_img = models.FileField(upload_to='adhaar/', null=True, blank=True)
    pan_no = models.CharField(max_length=100, null=True, blank=True)
    pan_img = models.FileField(upload_to='pancard/', null=True, blank=True)
    cancelled_check = models.FileField(upload_to='cancelled_check/', null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=100, null=True, blank=True)
    account_no = models.CharField(max_length=100, null=True, blank=True)
    branch = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name or ''}".strip()

    def save(self, *args, **kwargs):
        if self.profile_completed and not self.adhaar_no:
            raise ValueError("Aadhaar number must be added before marking profile as completed.")
        super().save(*args, **kwargs)


def generate_referral_code():
    """Generate a random 8-character alphanumeric referral code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))


class Franchise(models.Model):
    franchise_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    # staff = models.ForeignKey(StaffModel, on_delete=models.CASCADE,null=True, blank=True)
    franchise_name = models.CharField(max_length=255)
    franchise_owner = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    mobile_no = models.CharField(
        max_length=10,
        validators=[RegexValidator(
            regex=r'^\d{10}$', message="Enter a valid 10-digit mobile number.")]
    )
    password = models.CharField(max_length=128, null=True)
    referral_code = models.CharField(
        max_length=8, unique=True, default=generate_referral_code)
    aadhar = models.FileField(upload_to='files/')
    GST = models.FileField(upload_to='files/')
    pan = models.FileField(upload_to='files/')
    photo = models.FileField(upload_to='files/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Hash password only if it's not already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.franchise_name


class FranchiseWallet(models.Model):
    wallet_id = models.AutoField(primary_key=True)
    franchise = models.OneToOneField(
        Franchise, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.franchise.franchise_name} - ₹{self.balance}"


class WalletTransaction(models.Model):
    CREDIT = 'CREDIT'
    DEBIT = 'DEBIT'

    TRANSACTION_TYPES = [
        (CREDIT, 'Credit'),
        (DEBIT, 'Debit'),
    ]

    transaction_id = models.AutoField(primary_key=True)
    wallet = models.ForeignKey(
        FranchiseWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(null=True, blank=True)
    # Track who made this transaction (admin or staff)
    processed_by_admin = models.ForeignKey(
        AdminModel, on_delete=models.SET_NULL, null=True, blank=True)
    processed_by_staff = models.ForeignKey(
        StaffModel, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type}: ₹{self.amount} - {self.wallet.franchise.franchise_name}"
    


class LoanModel(models.Model):
    loan_id = models.AutoField(primary_key=True)
    loan_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.loan_name


class StatusModel(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.status_name


class BankModel(models.Model):
    bank_id = models.AutoField(primary_key=True)
    bank_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.bank_name


class StaffSelectionModel(models.Model):
    selection_id = models.AutoField(primary_key=True)
    selection = models.CharField(max_length=100)

    def __str__(self):
        return self.selection



class StaffAssignmentModel(models.Model):
    assignment_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    mobile_no = models.CharField(max_length=10)
    loan_type = models.CharField(max_length=100, null=True, blank=True)
    details = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assign_to = models.ForeignKey(
        StaffModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_to')
    assigned_by = models.ForeignKey(
        StaffModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_by')

    def __str__(self):
        return self.name


class LoanApplicationModel(models.Model):
    ACCEPT = 'Accept'
    REJECT = 'Reject'
    PENDING = 'Pending'
    REVIEW = 'Under Review'
    APPROVED = 'Approved'
    DISBURSED = 'Disbursed'
    
    STATUS_CHOICES = [
        (ACCEPT, 'Accept'),
        (REJECT, 'Reject'),
        (PENDING, 'Pending'),
        (REVIEW, 'Under Review'),
        (APPROVED, 'Approved'),
        (DISBURSED, 'Disbursed'),
    ]

    form_id = models.AutoField(primary_key=True)
    franchise = models.ForeignKey(Franchise, on_delete=models.CASCADE, null=True, blank=True)
    franchise_referral = models.CharField(max_length=8, null=True, blank=True)  
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    place = models.CharField(max_length=100, null=True, blank=True)
    phone_no = models.CharField(max_length=15, null=True, blank=True)

    guaranter_name = models.CharField(max_length=100, null=True, blank=True)
    guaranter_phoneno = models.CharField(max_length=50, null=True, blank=True)
    guaranter_job = models.CharField(max_length=100, null=True, blank=True)
    guaranter_cibil_score = models.CharField(max_length=50, null=True, blank=True)
    guaranter_cibil_issue = models.TextField(null=True, blank=True)
    guaranter_it_payable = models.BooleanField(default=False)
    guaranter_years = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    application_description = models.TextField(null=True, blank=True)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    workstatus = models.CharField(max_length=100, null=True, blank=True) 

    job = models.CharField(max_length=100, null=True, blank=True)
    cibil_score = models.CharField(max_length=100, null=True, blank=True)
    cibil_issue = models.TextField(null=True, blank=True)
    it_payable = models.BooleanField(default=False)
    year = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1900), MaxValueValidator(2100)])

    loan_amount = models.DecimalField(max_digits=10, default=0, decimal_places=2, null=True, blank=True)
    followup_date = models.DateField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status_name = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    executive_name = models.CharField(max_length=100, null=True, blank=True)
    mobileno_1 = models.CharField(max_length=15, null=True, blank=True)
    mobileno_2 = models.CharField(max_length=15, blank=True, null=True)
    assigned_to = models.ForeignKey(StaffModel, on_delete=models.SET_NULL, null=True, blank=True)
    document_description = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.franchise and self.franchise_referral:
            try:
                franchise = Franchise.objects.get(referral_code=self.franchise_referral)
                self.franchise = franchise
            except Franchise.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - Loan {self.loan_amount}"



class LoanStatusUpdateHistory(models.Model):
    """Track all status updates for loan applications"""
    history_id = models.AutoField(primary_key=True)
    loan_application = models.ForeignKey(
        LoanApplicationModel, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=20, null=True, blank=True)
    new_status = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)
    updated_by_admin = models.ForeignKey(
        AdminModel, on_delete=models.SET_NULL, null=True, blank=True)
    updated_by_staff = models.ForeignKey(
        StaffModel, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.loan_application.first_name} - {self.new_status} on {self.updated_at}"


class UploadedFile(models.Model):
    file_id = models.AutoField(primary_key=True)
    loan_application = models.ForeignKey(
        LoanApplicationModel, related_name='uploaded_files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/')
    file_type = models.CharField(max_length=50, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.loan_application.first_name} - {self.file_type}"
