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

class Transaction(models.Model):
    from_bank = models.ForeignKey(BankAccount, on_delete=models.CASCADE,related_name="from_bank")
    to_bank = models.ForeignKey(BankAccount, on_delete=models.CASCADE,related_name="to_bank")
    amount =  models.DecimalField(max_digits=100, decimal_places=2)
    transaction_date = models.DateField()
    creation_time = models.DateField()

    def save(self):
        if not self.creation_time:
            self.creation_time = date.today()
            self.from_bank.debit(self.amount)
            self.to_bank.credit(self.amount)
        return super().save()


def new_transaction(to_bank,from_bank,amount):
    new_transaction = Transaction()
    new_transaction.from_bank = from_bank
    new_transaction.to_bank = to_bank
    new_transaction.amount = amount
    new_transaction.transaction_date = date.today()
    new_transaction.save()

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
        for bank in BankAccount.objects.all().exclude(bank=self.salary_account.bank):
            new_transaction(bank, self.salary_account, bank.monthly_inflow)

    def undo_distribute(self):
        for bank in BankAccount.objects.all().exclude(bank=self.salary_account.bank):
            new_transaction(self.salary_account, bank, bank.monthly_inflow)
    
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
    creation_time = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name 

    def calculate(self):
        current_month = MoneyTracker.objects.get(month=calendar.month_name[self.date.month], year=self.date.year)
        current_month.expenses += self.amount
        current_month.save()

    def save(self):
        if not self.creation_time:
            self.creation_time = date.today()
            self.calculate()
            self.payment_mode.bank_account.debit(self.amount)
        return super().save()

@receiver(post_save,sender=Expense)
def recalculate(sender, instance, created, **kwargs):
    instance.calculate()


class InvestmentPortfolio(models.Model):
    name = models.CharField(max_length=100)
    details = models.TextField(max_length=500, blank=True)
    invested = models.DecimalField(default=0,decimal_places=2, max_digits=100)
    last_invested = models.DateField()
    current_value = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=100)
    last_updated = models.DateField(null=True, blank=True)
    roi = models.DecimalField(decimal_places=2, max_digits=20, null=True, blank=True)
    
    def __str__(self):
        return self.name

    def invest(self, amount):
        self.invested += amount
        self.current_value += amount
        self.save()

    def save(self):
        if self.current_value:
            self.roi = round(((self.current_value - self.invested) / self.invested)*100,2)
        self.last_updated = date.today()
        return super().save()


class Investment(models.Model):
    name = models.CharField(max_length=150, blank=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    investment_type = models.CharField(choices=INVESTMENT_TYPE, default="OTHER", max_length=100)
    comments = models.CharField(max_length=250, blank=True)
    portfolio = models.ForeignKey(InvestmentPortfolio, on_delete=models.CASCADE,related_name="investment_portfolio",blank=True, null=True)
    payment_mode = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE,related_name="investment_payment_method",blank=True, null=True)
    from_salary = models.BooleanField(default=True)
    creation_time = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return self.name

    def calculate(self):
        current_month = MoneyTracker.objects.get(month=calendar.month_name[self.date.month], year=self.date.year)
        current_month.invested += self.amount
        if not self.from_salary:
            current_month.actual_inhand += self.amount
        current_month.save()

    def save(self):
        if not self.creation_time:
            if self.from_salary:
                self.payment_mode.bank_account.debit(self.amount)
            self.calculate()
            self.portfolio.invest(self.amount)
        return super().save()

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