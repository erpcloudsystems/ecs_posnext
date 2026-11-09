from ecs_posnext.permissions import ensure_pos_permission_setup


def execute():
	# The same setup also runs on every migrate (after_migrate) - see
	# ecs_posnext.permissions for why a one-off patch is not enough.
	ensure_pos_permission_setup()
