from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
import mysql.connector

MYSQL_USER = 'root'
MYSQL_PASSWORD = '1'
MYSQL_HOST = '127.0.0.1'
MYSQL_DATABASE = 'employees'

class employee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    dept_data = None
    emp_data =None
    cnx = None

    @api.multi
    def action_sedot(self):
        self.process()

    def process(self):

        start = time.time()
        _logger.info("start time:%s", start)

        self.connect_mysql()
        self.pull_dept_mysql()
        total_dept = self.create_dept()

        self.pull_mysql_emp()
        total_emp = self.create_emp()

        end = time.time()

        self.cnx.disconnect()

        duration = (end-start)/60
        _logger.info("Total time:%s min, Total Emp rec:%s, Total dept:%s" , duration, total_emp, total_dept)


    def connect_mysql(self):
        self.cnx = mysql.connector.connect(user=MYSQL_USER,
                                password=MYSQL_PASSWORD,
                                host=MYSQL_HOST,
                                database=MYSQL_DATABASE)


    def pull_dept_mysql(self):
        cursor = self.cnx.cursor()
        sql = "select dept_no,dept_name from departments"
        cursor.execute(sql)
        self.dept_data = cursor.fetchall()

    def create_dept(self):
        cr = self.env.cr
        i = 0
        for dept in self.dept_data:
            sql = "select name from hr_department where name = %s and active = %s"
            cr.execute(sql, (dept[1], True))
            res = cr.fetchone()
            if not res:
                sql = "insert into hr_department (name, active) values (%s, %s)"
                cr.execute(sql, (dept[1], True))
                i = i + 1

        _logger.info("done create_dept")
        return i

    def pull_mysql_emp(self):
        cursor = self.cnx.cursor()

        sql = """select 
        e.emp_no,
        e.first_name,
        e.last_name,
        e.birth_date,
        e.gender,
        e.hire_date,
        d.dept_name

        from employees e
        left join dept_emp on dept_emp.emp_no = e.emp_no
        left join departments d on dept_emp.dept_no = d.dept_no
        """

        cursor.execute(sql)
        self.emp_data = cursor.fetchall()


    def create_emp(self):
        cr = self.env.cr
        i = 0

        for emp in self.emp_data:

            name = emp[1] + ' ' + emp[2]

            # resource_resource => resource_id
            sql = """insert into resource_resource (name, active, resource_type, time_efficiency, calendar_id, tz)
                values (%s, %s, %s, %s, %s, %s) 
                returning id
            """
            cr.execute(sql, (name, True, 'user', 100, 1, 'UTC'))
            res = cr.fetchone()
            if res and res[0]:
                resource_id = res[0]

            # hr_employee
            sql = """insert into hr_employee
             (identification_id, name, resource_id, birthday, gender, active, department_id)
            values (%s, %s, %s, %s, %s, %s, (select id from hr_department where name = %s and active = %s limit 1) )
            """

            cr.execute(sql, (emp[0], name, resource_id, emp[3], emp[4],True, emp[6], True ))

            i = i+1

        return i