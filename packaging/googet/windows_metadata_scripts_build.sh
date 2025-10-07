#!/bin/bash
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

version=$1

GUEST_AGENT_REPO="../google-guest-agent"

BUILD_DIR=$(pwd)
if [[ -d "$GUEST_AGENT_REPO" ]]; then
  pushd $GUEST_AGENT_REPO
  GOOS=windows VERSION=$version make cmd/gce_metadata_script_runner/gce_metadata_script_runner
  cp cmd/gce_metadata_script_runner/gce_metadata_script_runner $BUILD_DIR/google_metadata_script_runner/GCEMetadataScripts.exe
  popd
else
  GOOS=windows /tmp/go/bin/go build -ldflags '-X main.version={{.version}}' -mod=readonly -o ./google_metadata_script_runner/GCEMetadataScripts.exe ./google_metadata_script_runner
fi
