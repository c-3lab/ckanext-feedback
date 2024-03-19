# modify the permission of i18n/ja.js
docker exec -it ckan-docker-ckan-dev-1 bash -c "chmod 777 /srv/app/src/ckan/ckan/public/base/i18n/ja.js"
# pip install ckanext-feedback
docker exec -it ckan-docker-ckan-dev-1 bash -c "pip install /srv/app/src_extensions/ckanext-feedback"
# add ckanext-feedback to ckan.plugins
docker exec -it ckan-docker-ckan-dev-1 bash -c "sed -i '169s/$/ feedback/' /srv/app/ckan.ini"