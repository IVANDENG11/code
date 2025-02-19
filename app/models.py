from django.db import models

# Create your models here.
class User(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128)
    tel = models.CharField(max_length=128)
    password = models.CharField(max_length=128)

    class Meta:
        verbose_name_plural = '用户表'  # 此时，admin中表的名字就是‘用户表‘

class WeiBo(models.Model):
    id = models.AutoField(primary_key=True)

    content = models.CharField(max_length=256,verbose_name='商品评论')
    img = models.CharField(max_length=256,verbose_name='原始图片url')
    time = models.DateTimeField(verbose_name='评论时间')
    shuxing = models.CharField(max_length=128,verbose_name='商品属性')
    count = models.IntegerField(verbose_name='图片总数')
    other = models.IntegerField(verbose_name='其他数')
    pingfen = models.IntegerField(verbose_name='评论数')

    url = models.CharField(max_length=256, verbose_name='商品评论链接')
    emotion_chooice = (
        ('正向','正向'),
        ('负向','负向'),
    )

    name = models.CharField(max_length=128,verbose_name='用户昵称',default='')
    fenlei = models.CharField(max_length=128,verbose_name='发布位置',default='')
    topic = models.CharField(max_length=128,verbose_name='话题',default='')

    emotion = models.CharField(max_length=256, verbose_name='情感分类',choices=emotion_chooice,null=True)



    class Meta:
        verbose_name_plural = '商品评论表'  # 此时，admin中表的名字就是‘用户表‘





#####################################################下面可能是没用的

