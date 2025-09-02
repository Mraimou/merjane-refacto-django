from datetime import date
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .dto.product import ProcessOrderResponse
from .entities.order import Order
from .entities.product import Product
from .repositories.product_repository import pr
from .repositories.order_repository import or_
from .services.implementations.product_service import ps


class OrderProcessor:
    def __init__(self, order):
        self.order = order

    def process(self):
        for product in self.order.get_items():
            if product.type == "NORMAL":
                self._process_normal(product)
            elif product.type == "SEASONAL":
                self._process_seasonal(product)
            elif product.type == "EXPIRABLE":
                self._process_expirable(product)

    def _decrement(self, product):
        product.available -= 1

    def _save(self, product):
        product.save()

    def _process_normal(self, product):
        if product.available > 0:
            self._decrement(product)
            self._save(product)
        elif product.lead_time > 0:
            ps.notify_delay(product.lead_time, product)

    def _is_seasonal(self, product):
        is_seasonal = product.season_start_date < date.today() < product.season_end_date
        return product.available > 0 and is_seasonal

    def _process_seasonal(self, product):
        if self._is_seasonal(product):
            self._decrement(product)
            self._save(product)
        else:
            ps.handle_seasonal_product(product)

    def _is_expirable(self, product):
        return product.available > 0 and product.expiry_date > date.today()

    def _process_expirable(self, product):
        if self._is_expirable(product):
            self._decrement(product)
            self._save(product)
        else:
            ps.handle_expired_product(product)


@csrf_exempt
@require_POST
def process_order(request, order_id):
    # This part should be refactored as well
    order = or_.find_by_id(order_id).get()

    processor = OrderProcessor(order)
    processor.process()

    response = ProcessOrderResponse(order.id)
    return JsonResponse({"id": response.id}, status=200)

# @csrf_exempt
# @require_POST
# def process_order(request, order_id):
#     o = or_.find_by_id(order_id).get()
#     print(o)
#     ids = []
#     ids.append(order_id)
#     products = o.get_items()
#     for p in products:
#         if p.type == "NORMAL":
#             if p.available > 0:
#                 p.available = p.available - 1
#                 pr.save(p)
#             else:
#                 lead_time = p.lead_time
#                 if lead_time > 0:
#                     ps.notify_delay(lead_time, p)
#
#         elif p.type == "SEASONAL":
#             if (date.today() > p.season_start_date and date.today() < p.season_end_date and p.available > 0):
#                 p.available = p.available - 1
#                 pr.save(p)
#             else:
#                 ps.handle_seasonal_product(p)
#
#         elif p.type == "EXPIRABLE":
#             if p.available > 0 and p.expiry_date > date.today():
#                 p.available = p.available - 1
#                 pr.save(p)
#             else:
#                 ps.handle_expired_product(p)
#
#     response = ProcessOrderResponse(o.id)
#     return JsonResponse({'id': response.id}, status=200)
