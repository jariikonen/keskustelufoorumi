from db import db
import constants

def has_privilege(role, privilege, topic_privileges, user_mermberships):
    if role == constants.USER_ROLE__SUPER or role == constants.USER_ROLE__ADMIN:
        return True
    for membership in user_mermberships:
        if membership in topic_privileges.keys():
            if topic_privileges[membership][privilege]:
                return True
    return False
