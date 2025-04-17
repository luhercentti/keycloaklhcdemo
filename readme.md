
////////
minikube addons list | grep 'storage-provisioner'
minikube addons enable storage-provisioner

kubectl create namespace keycloak

helm repo add bitnami https://charts.bitnami.com/bitnami

helm repo update

helm install keycloak-postgres bitnami/postgresql \
  --namespace keycloak \
  --set auth.username=keycloak \
  --set auth.password=keycloak \
  --set auth.database=keycloak \
  --set persistence.enabled=true

# Wait for PostgreSQL to be ready
kubectl wait --namespace keycloak --for=condition=ready pod -l app.kubernetes.io/component=primary --timeout=300s


helm install keycloak bitnami/keycloak \
  --namespace keycloak \
  --set auth.adminUser=admin \
  --set auth.adminPassword=admin123 \
  --set postgresql.enabled=false \
  --set externalDatabase.host=keycloak-postgres-postgresql \
  --set externalDatabase.port=5432 \
  --set externalDatabase.user=keycloak \
  --set externalDatabase.password=keycloak \
  --set externalDatabase.database=keycloak

wait for keycloack to be up, can take some minutes, then load keycloak:
kubectl port-forward svc/keycloak 8080:80

now create the new client, with the redirect urls data 

//////// For the local docker test just do:
python -m venv keycloakdemo
source keycloakdemo/bin/activate

pip install -r requirements.txt

python3 app.py

//////////////////

