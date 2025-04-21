
docker-compose -f vault-docker-compose.yml up -d

helm install vault hashicorp/vault \
    --set "injector.enabled=true" \
    --set "server.enabled=false" \
    --set "injector.externalVaultAddr=http://host.docker.internal:8200" \
    --set "injector.hostNetwork=true"


vault write auth/kubernetes/config \
  kubernetes_host="$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')" \
  kubernetes_ca_cert=@"minikube-ca.crt" \
  token_reviewer_jwt="$TOKEN_REVIEW_JWT"


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
kubectl port-forward svc/keycloak 8080:80 -n keycloak

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
  redirect_uris="http://localhost:5000/callback" \
  flask_secret_key="aaaaaaaa"

this also contains the flask session encryption key, required for flask session to work securely "flask_secret_key"


vault policy write keycloakapp - <<EOF
path "keycloak/data/client-secrets" {
  capabilities = ["read"]
}
EOF

I have a Vault running in docker outside minikube, and for this demo i will install vault inyetor in my minikube
# Add the HashiCorp Helm repository
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Install the Vault Agent Injector
helm install vault hashicorp/vault \
    --set "injector.enabled=true" \
    --set "server.enabled=false" \
    --set "injector.externalVaultAddr=http://host.docker.internal:8200"
    --set "injector.serviceAccount.name=default"


docker build -t luhercen/python-keycloak-app:latest .

docker login 
docker push luhercen/python-keycloak-app:latest 
verify: https://hub.docker.com/repository/docker/luhercen/python-keycloak-app


kubectl apply -f k8s/deployment.yml


export VAULT_ADDR=http://0.0.0.0:8200


test connectivity from cluster to outside vault server:
kubectl run -it --rm vault-test --image=curlimages/curl --restart=Never -- \
  curl -v http://host.minikube.internal:8200/v1/sys/health
