[http://localhost:8001/docs](http://localhost:8001/docs)
[http://localhost:8002/docs](http://localhost:8002/docs)

kubectl delete pod api-gateway-68d465dc65-lzdcf

kubectl set image deployment/api-gateway api-gateway=api-gateway:v2

kubectl rollout undo deployment/api-gateway