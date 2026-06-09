NAMESPACE ?= intel-rh-demo
RELEASE ?= intel-inference

.PHONY: install uninstall template

install:
	helm upgrade --install $(RELEASE) . \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--set namespace=$(NAMESPACE) \
		$(EXTRA_HELM_ARGS)

uninstall:
	helm uninstall $(RELEASE) --namespace $(NAMESPACE)

template:
	helm template $(RELEASE) . \
		--namespace $(NAMESPACE) \
		--set namespace=$(NAMESPACE) \
		$(EXTRA_HELM_ARGS)
