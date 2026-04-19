from django.db import models
from commmon.models import UUIDTimeStampedModel
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
# Create your models here.


class QuoteStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SENT = "sent", "Sent"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"
    REVISED = "revised", "Revised"
    
class InvoiceStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SENT = "sent", "Sent"
    PAID = "paid", "Paid"
    OVERDUE = "overdue", "Overdue"
    CANCELLED = "cancelled", "Cancelled"
    
    
class Quote(UUIDTimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('revised', 'Revised'),
    ]

    # linked to either service request or project — not both
    service_request = models.OneToOneField(
        'services.ServiceRequest', on_delete=models.CASCADE, 
        null=True, blank=True, related_name='quotes'
    )
    project = models.OneToOneField(
        'projects.Project', on_delete=models.CASCADE,
        null=True, blank=True, related_name='quotes'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=QuoteStatus.choices, default='draft')
    quoted_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, related_name='quotes_given'
    )
    code = models.CharField(max_length=30, unique=True)  
    valid_until = models.DateField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    revision_count = models.PositiveIntegerField(default=0)  # how many times revised

    class Meta:
        ordering = ['-created_at']
        
    def revise(self, new_amount,user):
    # store history BEFORE changing
        QuoteRevisionHistory.objects.create(
            quote=self,
            old_amount=self.amount,
            new_amount=new_amount,
            revised_by=user,
        )

        # update current state
        self.amount = new_amount
        self.revision_count += 1
        self.status = "revised"

        self.save()

    def __str__(self):
        if self.service_request:
            return f"Quote for {self.service_request} — {self.amount}"
        return f"Quote for {self.project} — {self.amount}"

    def clean(self):
        # enforce only one is set
        if self.service_request and self.project:
            raise ValidationError('Quote can only be linked to either a service request or a project, not both.')
        if not self.service_request and not self.project:
            raise ValidationError('Quote must be linked to either a service request or a project.')
        
    def generate_code(self):
        now = datetime.now()
        
        year = now.strftime("%y")
        month = now.strftime("%m")
        day = now.strftime("%d")   
        time = now.strftime("%H%M%S")
        
        return f"BE-QT-{year}-{month}-{day}-{time}"
    
    def compute_total(self):
        total = self.items.aggregate(total=sum('total'))['total'] or 0
        self.amount = total

    def save(self, *args, **kwargs):
        if not self.code:  
            self.code = self.generate_code()
        if not self.valid_until:
            self.valid_until = date.today() + timedelta(weeks=2)
        super().save(*args, **kwargs)
        
        
class QuoteRevisionHistory(models.Model):
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name="revisions"
    )

    old_amount = models.DecimalField(decimal_places=2, max_digits=10)
    new_amount = models.DecimalField(decimal_places=2, max_digits=10)
    created_at = models.DateTimeField(auto_now_add=True)
    revised_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, related_name='quote_revisions'
    )

class QuoteItem(UUIDTimeStampedModel):
    quote = models.ForeignKey(
        Quote, on_delete=models.CASCADE, related_name='items'
    )
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    
    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price  # compute item total
        super().save(*args, **kwargs)
        self.quote.compute_total()  # trigger quote total after item saved
        
    def delete(self, *args, **kwargs):
        quote = self.quote  # store reference before deletion
        super().delete(*args, **kwargs)
        quote.compute_total()  # recompute after item deleted

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} — {self.total}"
    
    class Meta:
        ordering = ['-created_at']
        

        
class Invoice(UUIDTimeStampedModel):

    quote = models.OneToOneField(
        Quote, on_delete=models.PROTECT, 
        related_name='invoice',
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=InvoiceStatus.choices, default='draft')
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)
    code = models.CharField(max_length=30, unique=True)  # e.g. BE-INV-YYMMDD-HHMMSS

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invoice — {self.quote.code}"
    
    def generate_code(self):
        now = datetime.now()
        
        year = now.strftime("%y")
        month = now.strftime("%m")
        day = now.strftime("%d")   
        time = now.strftime("%H%M%S")
        
        return f"BE-INV-{year}-{month}-{day}-{time}"

    def save(self, *args, **kwargs):
        if not self.code:  
            self.code = self.generate_code()
        if not self.due_date:
            self.due_date = date.today() + timedelta(weeks=2)
        super().save(*args, **kwargs)
