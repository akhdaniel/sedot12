# -*- coding: utf-8 -*-
from odoo import http

# class Sedot-sql(http.Controller):
#     @http.route('/sedot-sql/sedot-sql/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sedot-sql/sedot-sql/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sedot-sql.listing', {
#             'root': '/sedot-sql/sedot-sql',
#             'objects': http.request.env['sedot-sql.sedot-sql'].search([]),
#         })

#     @http.route('/sedot-sql/sedot-sql/objects/<model("sedot-sql.sedot-sql"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sedot-sql.object', {
#             'object': obj
#         })