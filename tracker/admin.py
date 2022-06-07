from django.contrib import admin
from tracker.models import *
from django.contrib.auth.models import User, Group


class RefundAdmin(admin.ModelAdmin):
    list_display = ("source", "amount", "bank_account")
    list_filter = ("source", "date", "bank_account")
    exclude = ('creation_time',)


class BankAccountAdmin(admin.ModelAdmin):
    list_display = ("bank", "balance")
    change_list_template = "admin/add_distribute_buttons.html"

    def changelist_view(self, request, extra_context=None):
        total = BankAccount.objects.aggregate(total=Sum('balance'))['total']
        total_invested = InvestmentPortfolio.objects.aggregate(
            total=Sum("current_value"))["total"]
        context = {'total': str(round(total, 2)),
                   "invested": str(round(total_invested, 2)),
                   "total_worth": str(round(total + total_invested, 2))}
        return super(BankAccountAdmin, self).changelist_view(request, extra_context=context)


class SalaryModelAdmin(admin.ModelAdmin):
    list_display = ("name_of_the_company", "position", "in_hand_salary")
    change_list_template = "admin/add_admin_buttons.html"


class MoneyTrackerAdmin(admin.ModelAdmin):
    list_display = ("month", "year", "salary_model", "actual_inhand")
    change_list_template = "admin/add_admin_buttons.html"
    exclude = ('creation_time',)


class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("name", "expense_type", "amount", "comments")
    list_filter = ("expense_type", "date", "tags","payment_mode")
    change_list_template = "admin/add_admin_buttons.html"
    exclude = ('creation_time',)


class InvestmentAdmin(admin.ModelAdmin):
    list_display = ("name", "investment_type", "amount", "comments")
    list_filter = ("investment_type", "date","portfolio")
    change_list_template = "admin/add_admin_buttons.html"
    exclude = ('creation_time',)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "from_bank", "to_bank", "amount", "transaction_date")
    exclude = ('creation_time',)


class InvestmentPortfolioAdmin(admin.ModelAdmin):
    list_display = ("name", "invested", "current_value", "roi", "last_updated")


admin.site.register(BankAccount, BankAccountAdmin)
admin.site.register(PaymentMethod)
admin.site.register(SalaryModel, SalaryModelAdmin)
admin.site.register(MoneyTracker, MoneyTrackerAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Investment, InvestmentAdmin)
admin.site.register(Refund, RefundAdmin)
admin.site.register(ExpenseTypeTag)
admin.site.register(InvestmentPortfolio, InvestmentPortfolioAdmin)
admin.site.register(Transaction, TransactionAdmin)

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header = "Finanace Manager App"
admin.site.site_title = "Finanace Manager App"
admin.site.index_title = "Finanace Manager App"
