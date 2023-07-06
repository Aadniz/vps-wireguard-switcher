import dbus
import time


class Systemd:
    __has_inited = False

    # The connection to the system bus
    __sysbus = None
    # Local proxy for the given remote object
    __systemd1 = None
    # Proxy for the given interface on the given object
    __manager = None

    @staticmethod
    def __init():
        if Systemd.__has_inited:
            return

        Systemd.__sysbus = dbus.SystemBus()
        Systemd.__systemd1 = Systemd.__sysbus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        Systemd.__manager = dbus.Interface(Systemd.__systemd1, 'org.freedesktop.systemd1.Manager')
        Systemd.__has_inited = True

    @staticmethod
    def state(service) -> str | None:
        """
        Checks what state a systemd service is.
        :param service: The systemd name, including the .service at the end
        :return: active|inactive|activating|deactivating|failed|not-found|dead|None
        """
        Systemd.__init()

        try:
            unit = Systemd.__manager.GetUnit(service)
        except dbus.exceptions.DBusException:
            return None
        unit_obj = Systemd.__sysbus.get_object('org.freedesktop.systemd1', str(unit))
        unit_props = dbus.Interface(unit_obj, 'org.freedesktop.DBus.Properties')

        status = unit_props.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
        return str(status).lower().strip()

    @staticmethod
    def restart(service):
        """
        This function is async, you need to wait till the state has changed. Pulling the status in a while loop for example
        :param service: the systemd service name, including the .service at the end
        :return:
        """
        try:
            job_path = Systemd.__manager.RestartUnit(service, 'fail')
        except dbus.exceptions.DBusException as e:
            print(e)
        return
