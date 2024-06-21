# modify the permission of i18n/ja.js
docker exec -it ckan-docker-ckan-dev-1 bash -c "chmod 777 /srv/app/src/ckan/ckan/public/base/i18n/ja.js"
# pip install ckanext-feedback
docker exec -it ckan-docker-ckan-dev-1 bash -c "pip install /srv/app/src_extensions/ckanext-feedback"
# add ckanext-feedback to ckan.plugins
docker exec -it ckan-docker-ckan-dev-1 bash -c "sed -i 's/\(ckan\.plugins = .*\)/\1 feedback/' /srv/app/ckan.ini"
# initialize the database for feedback
docker exec -it ckan-docker-ckan-dev-1 bash -c "ckan db upgrade -p feedback"
# Copy ckan.datapusher.api_token setting value from ckan-dev to ckan-worker in ckan.ini
docker exec ckan-docker-ckan-dev-1 sh -c "grep '^ckan.datapusher.api_token' /srv/app/ckan.ini" | xargs -I {} docker exec ckan-docker-ckan-worker-1 sh -c "sed -i '/^\[app:main\]/a {}' /srv/app/ckan.ini"
# Restart to apply worker settings
docker restart ckan-docker-ckan-worker-1