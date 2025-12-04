from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import ActivityLike, ActivityComment, Profile, Notification

@receiver(post_save, sender=ActivityLike)
def create_like_notification(sender, instance, created, **kwargs):
    if created and instance.user != instance.activity.user:
        Notification.objects.create(
            recipient=instance.activity.user,
            sender=instance.user,
            notification_type='LIKE',
            activity=instance.activity
        )

@receiver(post_save, sender=ActivityComment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.user != instance.activity.user:
        Notification.objects.create(
            recipient=instance.activity.user,
            sender=instance.user,
            notification_type='COMMENT',
            activity=instance.activity
        )

@receiver(m2m_changed, sender=Profile.following.through)
def create_follow_notification(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for pk in pk_set:
            followed_profile = Profile.objects.get(pk=pk)
            Notification.objects.create(
                recipient=followed_profile.user,
                sender=instance.user,
                notification_type='FOLLOW'
            )
