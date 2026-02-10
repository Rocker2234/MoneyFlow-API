from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Account(models.Model):
    name = models.CharField(max_length=255)
    acc_no = models.BigIntegerField()
    ifsc_code = models.CharField(max_length=11)
    acc_type = models.CharField(max_length=50, verbose_name="Account Type")
    currency = models.CharField(max_length=3, verbose_name="Currency")
    min_bal = models.DecimalField(max_digits=16, decimal_places=2, default=0, db_default=0,
                                  validators=[MinValueValidator(Decimal(0.0), message="Minimum Balance cannot be < 0")],
                                  verbose_name="Minimum Balance")
    dis_bal = models.DecimalField(max_digits=16, decimal_places=2, default=0, db_default=0,
                                  validators=[MinValueValidator(Decimal(0.0), message="Desired Balance cannot be < 0")],
                                  verbose_name="Desired Balance")
    def_parser = models.CharField(max_length=20, blank=True, default='', verbose_name="Default Parser")
    def_grouper = models.CharField(max_length=40, blank=True, default='', verbose_name="Default Grouper")
    act_ind = models.BooleanField(default=True)
    isrt_dt = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    models.UniqueConstraint(fields=['acc_no', 'ifsc_code'], name='Unique Account')

    class Meta:
        ordering = ('name', 'acc_no',)

    def __str__(self) -> str:
        return self.name + ' - ' + str(self.acc_no)[-4:]


class CreditCard(models.Model):
    name = models.CharField(max_length=255)
    card_no = models.BigIntegerField()
    exp_date = models.DateField(verbose_name="Expiry Date")
    act_ind = models.BooleanField(default=True)
    isrt_dt = models.DateTimeField(auto_now_add=True, verbose_name="Inserted Date")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    models.UniqueConstraint(fields=['card_no', 'name'], name='Unique Credit Card')

    class Meta:
        verbose_name = "Credit Card"
        verbose_name_plural = "Credit Cards"

    def __str__(self) -> str:
        return self.name + ' - ' + str(self.card_no)[-4:]


class FileAudit(models.Model):
    file_name = models.CharField(max_length=32767)
    to_id = models.BigIntegerField()
    op_desc = models.CharField(max_length=255, verbose_name="Opreration Description")
    status = models.CharField(max_length=255)
    op_args = models.CharField(max_length=1024, blank=True, default='', verbose_name="Operation Arguments")
    op_add_txt = models.TextField(blank=True, default='', verbose_name="Operation Additional Text")
    updt_dt = models.DateTimeField(auto_now=True, verbose_name="Updated Date")
    isrt_dt = models.DateTimeField(auto_now_add=True, verbose_name="Inserted Date")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"

    def __str__(self):
        return f"{self.file_name} ({self.id})"


class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    txn_date = models.DateField(verbose_name="Transaction Date")
    txn_desc = models.CharField(max_length=1024, verbose_name="Transaction Description")
    grp_name = models.CharField(max_length=1024, blank=True, default='', verbose_name="Group Name")
    opr_dt = models.DateTimeField(verbose_name="Operation Date")
    dbt_amount = models.DecimalField(max_digits=16, decimal_places=2,
                                     validators=[MinValueValidator(Decimal(0.0), message="Debit amount cannot be < 0")],
                                     verbose_name="Debit Amount")
    cr_amount = models.DecimalField(max_digits=16, decimal_places=2,
                                    validators=[MinValueValidator(Decimal(0.0), message="Credit amount cannot be < 0")],
                                    verbose_name="Credit Amount")
    ref_num = models.CharField()
    cf_amt = models.DecimalField(max_digits=16, decimal_places=2,
                                 validators=[MinValueValidator(Decimal(0.0), message="CF amount cannot be < 0")],
                                 verbose_name="CF Amount")
    src_file = models.ForeignKey(FileAudit, on_delete=models.CASCADE, related_name='transactions',
                                 verbose_name="Source File")

    def __str__(self) -> str:
        return self.txn_desc


class CreditTransaction(models.Model):
    credit_card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='credit_transactions')
    txn_date = models.DateField(verbose_name="Transaction Date")
    txn_desc = models.CharField(max_length=1024, verbose_name="Transaction Description")
    grp_name = models.CharField(max_length=1024, blank=True, default='', verbose_name="Group Name")
    amt = models.DecimalField(max_digits=16, decimal_places=2, verbose_name='Amount')
    is_credit = models.BooleanField(default=False)
    src_file = models.ForeignKey(FileAudit, on_delete=models.CASCADE, related_name='credit_transactions',
                                 verbose_name="Source File")

    class Meta:
        verbose_name = "Credit Transaction"
        verbose_name_plural = "Credit Transactions"

    def __str__(self) -> str:
        return self.txn_desc
