from django.contrib import admin
from tracker.models import *
from  django.contrib.auth.models  import User, Group

class SalaryModelAdmin(admin.ModelAdmin):
    list_display = ("name_of_the_company","position", "in_hand_salary")
    change_list_template = "admin/add_admin_buttons.html"

class MoneyTrackerAdmin(admin.ModelAdmin):
    list_display = ("month","year", "salary_model", "actual_inhand" )
    change_list_template = "admin/add_admin_buttons.html"
    exclude = ('creation_time',)

class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("name","expense_type", "amount", "comments")
    list_filter = ("expense_type","date","tags")
    change_list_template = "admin/add_admin_buttons.html"

class InvestmentAdmin(admin.ModelAdmin):
    list_display = ("name","investment_type", "amount", "comments")
    list_filter = ("investment_type","date")
    change_list_template = "admin/add_admin_buttons.html"


admin.site.register(SalaryModel, SalaryModelAdmin)
admin.site.register(MoneyTracker, MoneyTrackerAdmin)
admin.site.register(Expense, ExpenseAdmin)
admin.site.register(Investment, InvestmentAdmin)
admin.site.register(ExpenseTypeTag)

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.site_header  =  "Finanace Manager App"  
admin.site.site_title  =  "Finanace Manager App"
admin.site.index_title  =  "Finanace Manager App"