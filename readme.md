
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
To work with minikube:

set password in hashicorp vault:

vault secrets enable -path=keycloak kv-v2

vault kv put keycloak/client-secrets \
  client_id="namegiventotheclientinkeycloakconsole" \
  client_secret="YOUR_CLIENT_SECRET" \
  auth_uri="http://keycloak-service.default.svc.cluster.local:8080/realms/testlhcrealm/protocol/openid-connect/auth" \
  token_uri="http://keycloak-service.default.svc.cluster.local:8080/realms/testlhcrealm/protocol/openid-connect/token" \
  userinfo_uri="http://keycloak-service.default.svc.cluster.local:8080/realms/testlhcrealm/protocol/openid-connect/userinfo" \
  issuer="http://keycloak-service.default.svc.cluster.local:8080/realms/testlhcrealm" \
  redirect_uris="http://localhost:5000/callback"


vault policy write keycloakapp - <<EOF
path "keycloak/data/client-secrets" {
  capabilities = ["read"]
}
EOF