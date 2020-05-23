# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

  $install_postfix = <<-SCRIPT
  export DEBIAN_FRONTEND=noninteractive
  export DEBIAN_PRIORITY=critical
  apt-get update -o quiet=2
  apt-get -y install postfix
  SCRIPT

  config.vm.define "milter-xmpp" do |box|
    box.vm.box = "ubuntu/bionic64"
    box.vm.box_version = "20200416.0.0"
    box.vm.hostname = "milter-xmpp.local"
    box.vm.network "private_network", ip: "192.168.61.55"
    box.vm.provision "shell", inline: $install_postfix
    box.vm.provider "virtualbox" do |vb|
      vb.gui = false
      vb.memory = 768
    end
  end
end
