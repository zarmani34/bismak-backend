from django.db import models

# Create your models here.
# apps/projects/models.py
from django.db import models
from commmon.models import UUIDTimeStampedModel
from accounts.models import User
from datetime import datetime

class ProjectStatus(models.TextChoices):
    PLANNING = "planning", "Planning"
    IN_PROGRESS = "in_progress", "In Progress"
    ON_HOLD = "on_hold", "On Hold"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Project(UUIDTimeStampedModel):    
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="projects")
    name = models.CharField(max_length=50)
    company = models.CharField(max_length=50) #This should be organisation not company name, we can fetch company name from organisation model using this field
    # type = models.CharField(max_length=50)  # Should be set to read only on serializer side as it will be set by views e.g Pressure Test, Leak Test, Calibration etc. To migrate later
    code = models.CharField(max_length=30, unique=True)
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.PLANNING
    )
    due_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} - {self.company}"
    
    def generate_code(self):
        now = datetime.now()
        
        year = now.strftime("%y")
        month = now.strftime("%m")
        day = now.strftime("%d")   
        time = now.strftime("%H%M%S")
        
        return f"BE-PR-{year}-{month}-{day}-{time}"

    def save(self, *args, **kwargs):
        if not self.code:  
            self.code = self.generate_code()
        super().save(*args, **kwargs)


class ProjectAssignment(UUIDTimeStampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="assignments"
    )
    assignee = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="project_assignments", limit_choices_to={"role__in": ["staff", "admin"]}
    )
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="assigned_projects", limit_choices_to={"role__in": ["admin"]})
    assignment_role = models.CharField(max_length=120, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["project", "assignee"], name="uniq_project_assignee"
            )
        ]
        
    def __str__(self):        
        return f"{self.project.code} | {self.assignee.get_full_name()} | {self.assignment_role}"
    
    

class TimelineEvent(UUIDTimeStampedModel):
    project = models.ForeignKey(Project, related_name='events', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='timeline_events')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.code} | {self.title}"
    
class PressureTest(UUIDTimeStampedModel):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='pressure_test')
    
    # Client & Location
    client = models.CharField(max_length=255)
    location_address = models.CharField(max_length=255)
    
    # Equipment Details
    manufacturer = models.CharField(max_length=255)
    manufacturing_date = models.DateField()
    serial_no = models.CharField(max_length=100, null=True, blank=True)
    truck_no = models.CharField(max_length=100)
    tank_capacity = models.DecimalField(max_digits=10, decimal_places=2)  # in litres
    product_stored = models.CharField(max_length=100, default='LPG')  # e.g LPG, PMS
    tank_type = models.CharField(max_length=100, default='Carbon Steel')  # e.g Carbon Steel
    
    # Test Details
    test_pressure = models.DecimalField(max_digits=8, decimal_places=2)  # in BAR
    working_pressure = models.DecimalField(max_digits=8, decimal_places=2)  # in BAR
    temperature = models.DecimalField(max_digits=5, decimal_places=2, default=40)  # in celsius
    test_duration = models.PositiveIntegerField(default=24)  # in hours
    test_medium = models.CharField(max_length=100, default='Hydrostatic')  # e.g Hydrostatic
    avrg_utm_gauge = models.DecimalField(max_digits=5, decimal_places=2)  # in MM
    
    # Safety Relief Valve
    safety_relief_valve_size = models.CharField(max_length=50)
    safety_relief_valve_no = models.PositiveIntegerField()
    
    # Dates
    date_of_test = models.DateField(default=datetime.now)
    next_test_date = models.DateField()
    
    # Result
    RESULT_CHOICES = [
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
    ]
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)

    def __str__(self):
        return f"Pressure Test — {self.project.code}"

    def save(self, *args, **kwargs):
        if not self.next_test_date:
            self.next_test_date = self.date_of_test.replace(year=self.date_of_test.year + 2)
        super().save(*args, **kwargs)

class LeakTest(UUIDTimeStampedModel):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='leak_test')
    
    # Client & Location
    station_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    
    # Test Details
    date_of_test = models.DateField()
    expiring_date = models.DateField()
    equipment_tested = models.CharField(max_length=255)  # e.g Underground Fuel Storage Tanks
    
    # Result
    RESULT_CHOICES = [
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
    ]
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)

    def __str__(self):
        return f"Leak Test — {self.project.code}"


class LeakTestTank(UUIDTimeStampedModel):
    """Each row in the leak test table"""
    leak_test = models.ForeignKey(LeakTest, on_delete=models.CASCADE, related_name='tanks')
    tank_no = models.PositiveIntegerField()
    product_stored = models.CharField(max_length=100)  # e.g PMS, AGO, DPK
    capacity = models.PositiveIntegerField()  # in litres
    age_of_tank = models.PositiveIntegerField()  # in years
    date_of_test = models.DateField()
    
    REMARK_CHOICES = [
        ('good', 'Good'),
        ('bad', 'Bad'),
        ('fair', 'Fair'),
    ]
    remark = models.CharField(max_length=20, choices=REMARK_CHOICES)

    class Meta:
        ordering = ['tank_no']

    def __str__(self):
        return f"Tank {self.tank_no} — {self.leak_test.project.code}"
# 
# create pressuretest model, calibration model, leaktest model etc 
# then link them with project type ND THEN PROJECT TYPE TO project using one-to-one relationship 