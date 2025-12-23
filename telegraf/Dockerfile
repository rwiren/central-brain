# ------------------------------------------------------------------------------
# Service: Telegraf Agent (Central Brain)
# Revision: 3.7.1
# ------------------------------------------------------------------------------
FROM telegraf:1.30

# Copy the configuration file
COPY telegraf.conf /etc/telegraf/telegraf.conf

# Start Telegraf
# (The default entrypoint handles variable expansion in the config)
CMD ["telegraf"]
