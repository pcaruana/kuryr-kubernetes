# Copyright (c) 2016 Mirantis, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys

from kuryr.lib._i18n import _LI
from oslo_log import log as logging
from oslo_service import service

from kuryr_kubernetes import clients
from kuryr_kubernetes import config
from kuryr_kubernetes import constants
from kuryr_kubernetes.handlers import dispatch as h_dis
from kuryr_kubernetes.handlers import k8s_base as h_k8s
from kuryr_kubernetes import watcher

LOG = logging.getLogger(__name__)


class KuryrK8sService(service.Service):
    """Kuryr-Kubernetes controller Service."""

    def __init__(self):
        super(KuryrK8sService, self).__init__()

        class DummyHandler(h_k8s.ResourceEventHandler):
            OBJECT_KIND = constants.K8S_OBJ_NAMESPACE

            def on_added(self, event):
                LOG.debug("added: %s",
                          event['object']['metadata']['selfLink'])

            def on_deleted(self, event):
                LOG.debug("deleted: %s",
                          event['object']['metadata']['selfLink'])

            def on_modified(self, event):
                LOG.debug("modified: %s",
                          event['object']['metadata']['selfLink'])

            def on_present(self, event):
                LOG.debug("present: %s",
                          event['object']['metadata']['selfLink'])

        pipeline = h_dis.EventPipeline()
        pipeline.register(DummyHandler())
        self.watcher = watcher.Watcher(pipeline, self.tg)
        self.watcher.add(constants.K8S_API_NAMESPACES)

    def start(self):
        LOG.info(_LI("Service '%s' starting"), self.__class__.__name__)
        super(KuryrK8sService, self).start()
        self.watcher.start()
        LOG.info(_LI("Service '%s' started"), self.__class__.__name__)

    def wait(self):
        super(KuryrK8sService, self).wait()
        LOG.info(_LI("Service '%s' stopped"), self.__class__.__name__)

    def stop(self, graceful=False):
        LOG.info(_LI("Service '%s' stopping"), self.__class__.__name__)
        self.watcher.stop()
        super(KuryrK8sService, self).stop(graceful)


def start():
    config.init(sys.argv[1:])
    config.setup_logging()
    clients.setup_clients()
    kuryrk8s_launcher = service.launch(config.CONF, KuryrK8sService())
    kuryrk8s_launcher.wait()