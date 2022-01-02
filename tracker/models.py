from django.db import models
import calendar
from django.db.models import Sum
from django.db.models.deletion import CASCADE
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


PAYMENT_METHODS = (
    ("Debit Card","Debit Card"),
    ("Net Banking","Net Banking"),
    ("UPI","UPI"),
    ("NEFT/IMPS","NEFT/IMPS"),
    ("Direct","Direct")
)


class BankAccount(models.Model):
    bank = models.CharField(max_length=25)
    monthly_inflow = models.IntegerField(default=0)
    balance = models.DecimalField(max_digits=100, decimal_places=2)

    def __str__(self):
        return self.bank

    def credit(self, amount):
        self.balance += amount
        self.save()

    def debit(self, amount):
        self.balance -= amount
        self.save()
    # def get_total(self):
    #     return BankAccount.objects.all().aggregate(Sum('balance'))["balance__sum"]

class PaymentMethod(models.Model):
    type = models.CharField(max_length=150, choices=PAYMENT_METHODS, default="Debit Card")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE,related_name="bank_payment_method")
    
    def __str__(self):
        return self.type + " - " + self.bank_account.bank

class SalaryModel(models.Model):
    in_hand_salary = models.IntegerField()
    name_of_the_company = models.CharField(max_length=150)
    position = models.CharField(max_length=100)
    amount_for_needs = models.DecimalField(max_digits=100, decimal_places=2, null=True,blank=True)
    amount_for_investments = models.DecimalField(max_digits=100, decimal_places=2,null=True, blank=True)
    amount_for_savings = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
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
    actual_inhand = models.DecimalField(max_digits=100, decimal_places=2)
    salary_model = models.ForeignKey(SalaryModel, on_delete=models.CASCADE,related_name="month_tracker")
    expenses = models.DecimalField(max_digits=100, decimal_places=2,default=0)
    invested = models.DecimalField(max_digits=100, decimal_places=2,default=0)
    saved = models.DecimalField(max_digits=100, decimal_places=2,default=0)
    creation_time = models.DateField(blank=True, null=True)
    salary_account = models.ForeignKey(BankAccount, on_delete=CASCADE,related_name="salary_account",blank=True, null=True)

    def __str__(self):
        return self.month + ", " + str(self.year)

    def distribute(self):
        total = BankAccount.objects.all().aggregate(Sum('monthly_inflow'))["monthly_inflow__sum"]
        self.salary_account.debit(total)
        for bank in BankAccount.objects.all():
            bank.credit(bank.monthly_inflow)

    def undo_distribute(self):
        total = BankAccount.objects.all().aggregate(Sum('monthly_inflow'))["monthly_inflow__sum"]
        self.salary_account.credit(total)
        for bank in BankAccount.objects.all():
            bank.debit(bank.monthly_inflow)
    
    def save(self):
        self.saved = self.actual_inhand - self.expenses - self.invested
        if not self.creation_time:
            self.creation_time = date.today()
            self.salary_account.credit(self.actual_inhand)
        return super().save()

class ExpenseTypeTag(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name



class Expense(models.Model):
    name = models.CharField(max_length=150, blank=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    expense_type = models.CharField(choices=EXPENSE_TYPE, default="Needs", max_length=100)
    tags = models.ManyToManyField(ExpenseTypeTag)
    comments = models.CharField(max_length=250, blank=True)
    payment_mode = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE,related_name="payment_method",blank=True, null=True)

    def __str__(self):
        return self.name 

    def calculate(self):
        current_month = MoneyTracker.objects.get(month=calendar.month_name[self.date.month], year=self.date.year)
        old_expenses = Expense.objects.filter(date__year = current_month.year, date__month = list(calendar.month_name).index(current_month.month))
        current_month.expenses = old_expenses.aggregate(Sum('amount'))["amount__sum"]
        current_month.save()

    def save(self):
        # self.calculate()
        self.payment_mode.bank_account.debit(self.amount)
        return super().save()

@receiver(post_save,sender=Expense)
def recalculate(sender, instance, created, **kwargs):
    instance.calculate()

class Investment(models.Model):
    name = models.CharField(max_length=150, blank=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    investment_type = models.CharField(choices=INVESTMENT_TYPE, default="OTHER", max_length=100)
    comments = models.CharField(max_length=250, blank=True)
    payment_mode = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE,related_name="investment_payment_method",blank=True, null=True)
    
    def __str__(self):
        return self.name

    def calculate(self):
        current_month = MoneyTracker.objects.get(month=calendar.month_name[self.date.month], year=self.date.year)
        old_investments = Investment.objects.filter(date__year = current_month.year, date__month = list(calendar.month_name).index(current_month.month))
        current_month.invested = old_investments.aggregate(Sum('amount'))["amount__sum"]
        current_month.save()

    def save(self):
        self.payment_mode.bank_account.debit(self.amount)
        return super().save()
    
    def post_save(self):
        self.calculate()
        print("Post save")

@receiver(post_save,sender=Investment)
def recalculate(sender, instance, created, **kwargs):
    instance.calculate()

class Refund(models.Model):
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    source = models.CharField(max_length=250)
    bank_account = models.ForeignKey(BankAccount, on_delete=CASCADE,related_name="refund_bank_account",blank=True, null=True)
    date = models.DateField()
    creation_time = models.DateField(null=True, blank=True)

    def save(self):
        if not self.creation_time:
            self.creation_time = self.date
            self.bank_account.credit(self.amount)
        return super().save()