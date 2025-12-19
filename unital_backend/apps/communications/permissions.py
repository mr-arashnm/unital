from rest_framework.permissions import BasePermission


class IsTicketParticipantOrStaff(BasePermission):
    """Permission for SupportTicket object access.

    Allow access if the user is:
    - manager/board_member/staff (admin roles), OR
    - the ticket submitter, OR
    - the assigned user, OR
    - a member of the ticket's team (if set).
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.user_type in ['manager', 'board_member', 'staff']:
            return True

        if obj.submitted_by_id == user.id:
            return True

        if obj.assigned_to_id and obj.assigned_to_id == user.id:
            return True

        if getattr(obj, 'team', None):
            try:
                return obj.team.members.filter(id=user.id).exists()
            except Exception:
                return False

        return False
