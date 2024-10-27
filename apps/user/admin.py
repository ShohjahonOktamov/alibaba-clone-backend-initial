from django.contrib import admin

from .models import User, Group, Policy, SellerUser, BuyerUser


# Register your models here.

class PolicyAdmin(admin.ModelAdmin):
    list_display: tuple[str, str] = "id", "name", "is_active"


class GroupAdmin(admin.ModelAdmin):
    list_display: tuple[str, str] = "id", "name", "is_active"


admin.site.register(User)
admin.site.register(Group, GroupAdmin)
admin.site.register(Policy, PolicyAdmin)
admin.site.register(SellerUser)
admin.site.register(BuyerUser)
