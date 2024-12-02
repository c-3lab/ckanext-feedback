# modify the permission of i18n/ja.js
docker exec -it ckan-docker-ckan-dev-1 bash -c "chmod 777 /srv/app/src/ckan/ckan/public/base/i18n/ja.js"
# pip install ckanext-feedback
docker exec -it ckan-docker-ckan-dev-1 bash -c "pip install /srv/app/src_extensions/ckanext-feedback"
# add ckanext-feedback to ckan.plugins
docker exec -it ckan-docker-ckan-dev-1 bash -c "sed -i 's/\(ckan\.plugins = .*\)/\1 feedback/' /srv/app/ckan.ini"
# initialize the database for feedback
docker exec -it ckan-docker-ckan-dev-1 bash -c "ckan db upgrade -p feedback"
# Copy the ckan.ini file from the ckan-docker-ckan-dev-1 container to the host's /tmp directory
docker cp ckan-docker-ckan-dev-1:/srv/app/ckan.ini /tmp/ckan.ini
# Remove the "feedback" plugin from the "ckan.plugins" setting in the copied ckan.ini file
sed -i '/^ckan.plugins = /s/ feedback//' /tmp/ckan.ini
# Copy the modified ckan.ini file back to the ckan-docker-ckan-worker-1 container, overwriting the existing one
docker cp /tmp/ckan.ini ckan-docker-ckan-worker-1:/srv/app/ckan.ini
# Delete the temporary /tmp/ckan.ini file used for the modification
rm /tmp/ckan.ini
# Restart to apply worker settings
docker restart ckan-docker-ckan-worker-1