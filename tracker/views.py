from django.shortcuts import render
from .models import *
from django.http import HttpResponse, HttpResponseRedirect
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.contrib import messages


def get_total_report():
    total_actual_invested = MoneyTracker.objects.aggregate(Sum('invested'))[
        "invested__sum"]
    total_invested = MoneyTracker.objects.exclude(
        month="August", year=2021).aggregate(Sum('invested'))["invested__sum"]
    total_spent = MoneyTracker.objects.aggregate(Sum('expenses'))[
        "expenses__sum"]
    total_saved = MoneyTracker.objects.aggregate(Sum('saved'))["saved__sum"]
    total_inhand = MoneyTracker.objects.aggregate(
        Sum('actual_inhand'))["actual_inhand__sum"]
    num_months = len(MoneyTracker.objects.all()) - 1
    data = {
        "total": {
            "total_investment": total_actual_invested,
            "total_spent": total_spent,
            "total_saved": total_saved,
        },
        "average": {
            "avg_invested": round(total_invested/num_months, 2) if num_months != 0 else total_invested,
            "avg_spent": round(total_spent/num_months, 2) if num_months != 0 else total_spent,
            "avg_saved": round(total_saved/num_months, 2) if num_months != 0 else total_saved,
            "avg_inhand": round(total_inhand/num_months, 2) if num_months != 0 else total_inhand
        },
        "percentage": {
            "perc_invested": round(total_invested*100/total_inhand, 2),
            "perc_spent": round(total_spent*100/total_inhand, 2),
            "perc_saved": round(total_saved*100/total_inhand, 2),
        }
    }
    return data


def get_specific_data(selected_month, selected_year):
    try:
        tracker_object = MoneyTracker.objects.get(
            month=selected_month, year=selected_year)
        data = {
            "invested": tracker_object.invested,
            "spent": tracker_object.expenses,
            "saved": tracker_object.saved,
        }
    except:
        data = None
    return data


def get_monthly_report():
    all_data = MoneyTracker.objects.all().exclude(
        month="August", year=2021).order_by('-creation_time')
    data = []
    for monthly_tracker in all_data:
        data_key = monthly_tracker.month + " - " + str(monthly_tracker.year)
        var_key = monthly_tracker.month.lower() + "_" + str(monthly_tracker.year)
        data.append({
            'name': data_key,
            'var_name': var_key,
            "data": get_specific_data(monthly_tracker.month, monthly_tracker.year)
        })
    return data


@login_required
def get_analytics(request):
    context = {
        "overall_data": get_total_report(),
        "monthly_report": get_monthly_report()
    }
    return render(request, "tracker/dashboard.html", context)


def get_monthly_analytics(request, month, year):
    month = month.capitalize()
    context = {
        "data": get_specific_data(month, year)
    }
    return HttpResponse(str(context))


def get_investments_by_type(investments):
    result = dict()
    result["total_invested_amount"] = investments.aggregate(Sum('amount'))[
        "amount__sum"]
    result["distribution"] = []
    for investment_type in INVESTMENT_TYPE:
        filtered_investments = investments.filter(
            investment_type=investment_type[0])
        investment_data = {
            "name": investment_type[0].lower().capitalize(),
            "amount": filtered_investments.aggregate(Sum('amount'))["amount__sum"]
        }
        result["distribution"].append(investment_data)
    return result


def get_investments_by_month(investments):
    all_data = MoneyTracker.objects.exclude(
        month="August", year=2021).order_by('-creation_time')
    data = []
    for monthly_tracker in all_data:
        filtered_investments = investments.filter(date__year=monthly_tracker.year, date__month=list(
            calendar.month_name).index(monthly_tracker.month))
        data_key = monthly_tracker.month + " - " + str(monthly_tracker.year)
        var_key = monthly_tracker.month.lower() + "_" + str(monthly_tracker.year)
        data.append({
            "name": data_key,
            "var_name": var_key,
            "investments": get_investments_by_type(filtered_investments)
        })
    return data


def get_investment_summary(request):
    all_investments = Investment.objects.all()
    context = {
        "data": {
            "investments_by_types": get_investments_by_type(all_investments),
            "investments_by_month": get_investments_by_month(all_investments)
        }
    }
    return render(request, "tracker/investments.html", context)


def get_expenses_by_type(expenses):
    result = []
    for expense_type in EXPENSE_TYPE:
        filtered_expenses = expenses.filter(expense_type=expense_type[0])
        result.append({
            "name": expense_type[0],
            "amount": filtered_expenses.aggregate(Sum('amount'))["amount__sum"]
        })
    return result


def get_expenses_by_tag(expenses):
    tags = ExpenseTypeTag.objects.all()
    res = []
    for tag in tags:
        filtered_expenses = expenses.filter(tags=tag)
        amount_spent = filtered_expenses.aggregate(Sum('amount'))[
            "amount__sum"]
        res.append({
            "name": tag.name,
            "amount": amount_spent if amount_spent else 0
        })
    return res


def get_expense_summary(request):
    all_expenses = Expense.objects.all()
    data = []
    all_data = MoneyTracker.objects.exclude(
        month="August", year=2021).order_by('-creation_time')
    for monthly_tracker in all_data:
        filtered_expenses = all_expenses.filter(date__year=monthly_tracker.year, date__month=list(
            calendar.month_name).index(monthly_tracker.month))
        data_key = monthly_tracker.month + " - " + str(monthly_tracker.year)
        var_key = monthly_tracker.month.lower() + "_" + str(monthly_tracker.year)
        total_spent_amount = filtered_expenses.aggregate(Sum('amount'))[
            "amount__sum"]
        expenses_by_type = get_expenses_by_type(filtered_expenses)
        expenses_by_tag = get_expenses_by_tag(filtered_expenses)
        data.append({
            "name": data_key,
            "var_name": var_key,
            "amount": total_spent_amount,
            "expenses_by_type": expenses_by_type,
            "expenses_by_tag": expenses_by_tag
        })

    return render(request, "tracker/expenses.html", context={"data": data})


def funds_distribute(request):
    messages.info(request, 'Your funds has been distributed successfully!')
    current_month = MoneyTracker.objects.get(
        month=calendar.month_name[datetime.now().month], year=datetime.now().year)
    current_month.distribute()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def undo_funds_distribute(request):
    current_month = MoneyTracker.objects.get(
        month=calendar.month_name[datetime.now().month], year=datetime.now().year)
    current_month.undo_distribute()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
