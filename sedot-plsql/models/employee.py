from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError
import logging
import os
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

    @api.model_cr
    def init(self):
        _logger.info("creating functions...")
        self.env.cr.execute("""
DROP FUNCTION IF EXISTS vit_create_emp(TEXT);
CREATE OR REPLACE FUNCTION vit_create_emp(data TEXT)
RETURNS VOID AS $BODY$
DECLARE
	records TEXT[];
	rec TEXT;
	emp_rec TEXT[];
	v_emp_no TEXT;
	v_first_name TEXT;
	v_last_name TEXT;
	v_birth_date TEXT;
	v_gender TEXT;
	v_hire_date TEXT;
	v_department TEXT;
	v_resource_id INTEGER;
	v_emp_exist TEXT;
BEGIN
	SELECT string_to_array(data, '|') INTO records;
	FOREACH rec IN ARRAY records LOOP
		SELECT string_to_array(rec, '~~') INTO emp_rec;
		v_emp_no = emp_rec[1];
		v_first_name = emp_rec[2];
		v_last_name = emp_rec[3];
		v_birth_date = emp_rec[4];
		v_gender = emp_rec[5];
		v_hire_date = emp_rec[6];
		v_department = emp_rec[7];


        SELECT identification_id from hr_employee where identification_id = v_emp_no INTO v_emp_exist;
        
        IF v_emp_exist IS NULL THEN
            -- insert the resources
            insert into resource_resource (name, active, resource_type, time_efficiency, calendar_id, tz)
                    values (v_first_name||' '||v_last_name, true, 'user', 100, 1, 'UTC') 
                    returning id INTO v_resource_id;
    
            -- insert hr_employee
    
            insert into hr_employee (identification_id, name, resource_id, birthday, gender, active, department_id)
            values (v_emp_no, v_first_name||' '||v_last_name, v_resource_id, TO_DATE(v_birth_date, 'YYYY-MM-DD'), 
            v_gender, true, 
            (select id from hr_department where name = v_department and active = true limit 1) );
            
        ELSE
            UPDATE hr_employee SET name = v_first_name||' '||v_last_name,
                birthday = TO_DATE(v_birth_date, 'YYYY-MM-DD')
                WHERE identification_id = v_emp_no;
                
        END IF;
        
		RAISE NOTICE 'create emp %', v_first_name;
		
	END LOOP;
END;

$BODY$
LANGUAGE plpgsql;

DROP FUNCTION IF EXISTS vit_create_dept(TEXT);
CREATE OR REPLACE FUNCTION vit_create_dept(data TEXT)
RETURNS VOID AS $BODY$
DECLARE
	records TEXT[];
	rec TEXT;
	dept_rec TEXT[];
	v_dept_no TEXT;
	v_dept_name TEXT;
	v_dept_exist TEXT;
	
BEGIN

	--- d009~~Customer Service|d005~~Development|d002~~Finance|d003~~Human Resources|d001~~Marketing|d004~~Production|d006~~Quality Management|d008~~Research|d007~~Sales 

	SELECT string_to_array(data, '|') INTO records;

	FOREACH rec IN ARRAY records LOOP
		SELECT string_to_array(rec, '~~') INTO dept_rec;
		v_dept_no = dept_rec[1];
		v_dept_name = dept_rec[2];

		RAISE NOTICE 'dept no = %', v_dept_no;
		RAISE NOTICE 'dept name = %', v_dept_name;

		select name from hr_department where name = v_dept_name and active = true limit 1 into v_dept_exist;
		IF v_dept_exist IS NULL THEN
			insert into hr_department (name, active) values (v_dept_name, true);
		END IF;
	END LOOP;
END;
$BODY$
LANGUAGE plpgsql;


        """)

    @api.multi
    def action_sedot(self):
        self.process()

    def process(self):

        start = time.time()
        _logger.info("start time:%s", start)

        self.connect_mysql()
        self.pull_dept_mysql()
        total_dept = self.create_dept()


        last_update = self.env['ir.config_parameter'].sudo().get_param('vit.last_update')
        self.pull_mysql_emp(last_update)
        total_emp = self.create_emp()

        end = time.time()

        os.environ["TZ"] = "Asia/Jakarta"
        self.env['ir.config_parameter'].sudo().set_param('vit.last_update', time.strftime("%Y-%m-%d %H:%M:%S"))

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
        data_final = []

        # 001~~depart1|002~~depart2|003~~depart3|......
        for dept in self.dept_data:
            recs = [ str(d) for d in dept]
            recs = "~~".join(recs)
            data_final.append(recs)
            i = i + 1

        data_final = "|".join(data_final)
        _logger.info("data_final=%s", data_final)
        cr.execute("select vit_create_dept(%s)", (data_final,))
        _logger.info("done create_dept")
        return i

    def pull_mysql_emp(self, last_update):
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
        
        where e.last_update > %s
        """

        cursor.execute(sql, (last_update, ))
        self.emp_data = cursor.fetchall()


    def create_emp(self):
        cr = self.env.cr
        i = 0
        data_final = []

        for emp in self.emp_data:
            recs = [ str(e) for e in emp]
            recs = "~~".join(recs)
            data_final.append(recs)
            i = i+1

        data_final = "|".join(data_final)
        _logger.info("data_final=%s", data_final)
        cr.execute("select vit_create_emp(%s)", (data_final,))

        return i


    def cron_import(self):
        self.process()
        
