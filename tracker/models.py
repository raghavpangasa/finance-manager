from django.db import models
import calendar
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import  receiver
from datetime import date

INVESTMENT_TYPE = (
    ("GOLD", "GOLD"),
    ("MUTUAL FUNDS", "MUTUAL FUNDS"),
    ("SMALLCASE", "SMALLCASE"),
    ("STOCKS", "STOCKS"),
    ("CRYPTO", "CRYPTO"),
    ("PPF", "PPF"),
    ("OTHER", "OTHER")
)

EXPENSE_TYPE = (
    ("Needs", "Needs"),
    ("Wants", "Wants"),
)

MONTHS = (
    ("January","January"),
    ("February","February"),
    ("March","March"),
    ("April","April"),
    ("May","May"),
    ("June","June"),
    ("July","July"),
    ("August","August"),
    ("September","September"),
    ("October","October"),
    ("November","November"),
    ("December","December")
)

class SalaryModel(models.Model):
    in_hand_salary = models.IntegerField()
    name_of_the_company = models.CharField(max_length=150)
    position = models.CharField(max_length=100)
    amount_for_needs = models.FloatField(null=True,blank=True)
    amount_for_investments = models.FloatField(null=True, blank=True)
    amount_for_savings = models.FloatField(null=True, blank=True)
    start_month = models.DateField()
    end_month = models.DateField(null=True, blank=True)

    def save(self):
        self.amount_for_needs = 0.3 * self.in_hand_salary
        self.amount_for_investments = 0.5 * self.in_hand_salary
        self.amount_for_savings = 0.2 * self.in_hand_salary
        return super().save()

    def __str__(self):
        return self.name_of_the_company + " : " + self.position


class MoneyTracker(models.Model):
    month = models.CharField(max_length=150, choices=MONTHS, default="January")
    year = models.IntegerField(default=2021)
    actual_inhand = models.FloatField()
    salary_model = models.ForeignKey(SalaryModel, on_delete=models.CASCADE,related_name="month_tracker")
    expenses = models.FloatField(default=0)
    invested = models.FloatField(default=0)
    saved = models.FloatField(default=0)
    creation_time = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.month + ", " + str(self.year)
    
    def save(self):
        self.saved = self.actual_inhand - self.expenses - self.invested
        if not self.creation_time:
            self.creation_time = date.today()
        return super().save()

class ExpenseTypeTag(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name




class Expense(models.Model):
    name = models.CharField(max_length=150, blank=True)
    date = models.DateField()
    amount = models.FloatField()
    expense_type = models.CharField(choices=EXPENSE_TYPE, default="Needs", max_length=100)
    tags = models.ManyToManyField(ExpenseTypeTag)
    comments = models.CharField(max_length=250, blank=True)

    def __str__(self):
        return self.name 

    def calculate(self):
        current_month = MoneyTracker.objects.get(month=calendar.month_name[self.date.month], year=self.date.year)
        old_expenses = Expense.objects.filter(date__year = current_month.year, date__month = list(calendar.month_name).index(current_month.month))
        current_month.expenses = old_expenses.aggregate(Sum('amount'))["amount__sum"]
        current_month.save()

    def save(self):
        # self.calculate()
        return super().save()

@receiver(post_save,sender=Expense)
def recalculate(sender, instance, created, **kwargs):
    instance.calculate()

class Investment(models.Model):
    name = models.CharField(max_length=150, blank=True)
    date = models.DateField()
    amount = models.FloatField()
    investment_type = models.CharField(choices=INVESTMENT_TYPE, default="OTHER", max_length=100)
    comments = models.CharField(max_length=250, blank=True)
    
    def __str__(self):
        return self.name

    def calculate(self):
        current_month = MoneyTracker.objects.get(month=calendar.month_name[self.date.month], year=self.date.year)
        old_investments = Investment.objects.filter(date__year = current_month.year, date__month = list(calendar.month_name).index(current_month.month))
        current_month.invested = old_investments.aggregate(Sum('amount'))["amount__sum"]
        current_month.save()

    def save(self):
        return super().save()
    
    def post_save(self):
        self.calculate()
        print("Post save")

@receiver(post_save,sender=Investment)
def recalculate(sender, instance, created, **kwargs):
    instance.calculate()
