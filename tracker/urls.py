from django.urls import path
from . import views

urlpatterns = [
    path("", views.get_analytics, name="dashboard"),
    path("<str:month>/<int:year>", views.get_monthly_analytics,
         name="monthly-analytics"),
    path("investments/", views.get_investment_summary, name="investment-summary"),
    path("expenses/", views.get_expense_summary, name="expense-summary"),
    path("distribute/", views.funds_distribute, name="funds-distribute"),
    path("undo_distribute/", views.undo_funds_distribute,
         name="undo-funds-distribute")
]
