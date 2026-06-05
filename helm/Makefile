NAMESPACE ?= intel-rh-demo
RELEASE ?= intel-inference

.PHONY: install uninstall template

install:
	helm upgrade --install $(RELEASE) . \
		--namespace $(NAMESPACE) \
		--create-namespace \
		$(EXTRA_HELM_ARGS)

uninstall:
	helm uninstall $(RELEASE) --namespace $(NAMESPACE)

template:
	helm template $(RELEASE) . \
		--namespace $(NAMESPACE) \
		$(EXTRA_HELM_ARGS)
