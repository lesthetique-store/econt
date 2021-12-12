# econt
A library for use econt.com delivery service

#### Install
```bash
pip install econt
```

#### Example

```python
from econt.api import Econt
econt = Econt()
econt.get_countries()
econt.get_cities()
econt.get_offices()
econt.get_streets()
econt.get_streets_by_city(city_post_code="1407")
econt.get_offices_by_city(city_post_code="1407")
econt.get_quarters()
econt.get_seller_addresses()
econt.get_regions()
econt.get_clients()
```