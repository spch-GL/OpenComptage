import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots

from datetime import datetime, timedelta
from functools import partial

from qgis.PyQt.QtWidgets import QDockWidget, QListWidgetItem, QTabWidget
from qgis.core import QgsMessageLog, Qgis
from comptages.core.utils import get_ui_class, push_info
from comptages.ui.resources import *
from comptages.core import statistics, definitions
from comptages.datamodel import models

FORM_CLASS = get_ui_class("chart_dock.ui")


class ChartDock(QDockWidget, FORM_CLASS):
    def __init__(self, iface, layers, parent=None):
        QDockWidget.__init__(self, parent)
        self.setupUi(self)
        self.layers = layers
        self.count = None
        self.sensor = None

    def set_attributes(self, count: models.Count):
        self.count = count

        self.setWindowTitle(
            "Comptage: {}, installation: {}".format(
                count.id, count.id_installation.name
            )
        )

        # Exit and show message if there are no data to show
        if not models.CountDetail.objects.filter(id_count=count).exists():
            self.hide()
            push_info(
                "Installation {}: Il n'y a pas de données à montrer pour "
                "le comptage {}".format(count.id_installation.name, count.id)
            )
            QgsMessageLog.logMessage(
                "{} - Generate chart action : No data for count {}".format(
                    datetime.now(), count.id
                ),
                "Comptages",
                Qgis.Info,
            )
            return

        self.show()

        self.buttonSet.clicked.connect(self.set_dates)
        self.buttonReset.clicked.connect(self.reset_dates)

        qs = models.CountDetail.objects.filter(
            id_count=self.count,
        )

        self.startDate.setDateTime(qs.earliest("timestamp").timestamp)
        self.endDate.setDateTime(qs.latest("timestamp").timestamp)

        self._create_tabs(count)

    def _create_tabs(self, count: models.Count):
        try:
            self.tabWidget.currentChanged.disconnect(self.current_tab_changed)
        except Exception:
            pass

        self.tabWidget.clear()
        self.tabWidget.currentChanged.connect(self.current_tab_changed)

        # We do by section and not by count because of special cases.
        sections = models.Section.objects.filter(
            lane__id_installation__count=count
        ).distinct()
        for section in sections:
            tab = ChartTab()
            self.tabWidget.addTab(tab, section.id)
            self._populate_tab(tab, section, count)

    def _populate_tab(self, tab, section: models.Section, count: models.Count):
        # Check if there is data to be validated
        approval_process = False
        if models.CountDetail.objects.filter(
            id_count=count, import_status=definitions.IMPORT_STATUS_QUARANTINE
        ).exists():
            approval_process = True
        # Remove previous items
        try:
            tab.chartList.currentRowChanged.disconnect(self.chart_list_changed)
        except Exception:
            pass
        QgsMessageLog.logMessage(
            "{} - Debug_GL: Graphique démarré".format(datetime.now()),
            "Comptages",
            Qgis.Info,
        )

        for i in range(tab.chartList.count()):
            tab.chartList.takeItem(0)
        tab.chartList.currentRowChanged.connect(self.chart_selection_changed)

        if approval_process:
            tab.buttonValidate.show()
            tab.buttonValidate.clicked.connect(partial(self.validate_count, section))
            tab.buttonRefuse.clicked.connect(partial(self.refuse_count, section))
            tab.buttonRefuse.show()
        else:
            tab.buttonValidate.hide()
            tab.buttonRefuse.hide()

        sensor_type: models.SensorType = count.id_sensor_type
        lanes = models.Lane.objects.filter(id_section=section)
        directions = (
            lanes.values("direction").distinct().values_list("direction", flat=True)
        )

        start = self.startDate.date().toPyDate()
        end = self.endDate.date().toPyDate() + timedelta(days=1)

        if sensor_type.name == "Boucle":
            # By lane
            for i, lane in enumerate(lanes):
                tab.chartList.addItem(
                    QListWidgetItem("Par heure, voie {}".format(lane.number))
                )
                tab.charts.append(
                    ChartTime(
                        count=count,
                        section=section,
                        lane=lane,
                        start=start,
                        end=end,
                    ).get_div()
                )

        else:
            # By direction
            for i, direction in enumerate(directions):
                tab.chartList.addItem(
                    QListWidgetItem("Par heure, direction {}".format(direction))
                )
                tab.charts.append(
                    ChartTime(
                        count=count,
                        section=section,
                        direction=direction,
                        start=start,
                        end=end,
                    ).get_div()
                )

        tab.chartList.addItem(QListWidgetItem("Par catégorie"))
        tab.charts.append(
            ChartCat(
                count=count,
                section=section,
                start=start,
                end=end,
            ).get_div()
        )

        tab.chartList.addItem(QListWidgetItem("Par vitesse"))
        tab.charts.append(
            ChartSpeed(
                count=count,
                section=section,
                start=start,
                end=end,
            ).get_div()
        )

        if sensor_type.name == "Boucle":
            # By lane
            for i, lane in enumerate(lanes):
                tab.chartList.addItem(
                    QListWidgetItem("Par TJM, voie {}".format(lane.number))
                )
                tab.charts.append(
                    ChartTjm(
                        count=count,
                        section=section,
                        lane=lane,
                        start=start,
                        end=end,
                    ).get_div()
                )

        else:
            # By direction
            for i, direction in enumerate(directions):
                tab.chartList.addItem(
                    QListWidgetItem("Par TJM, direction {}".format(direction))
                )
                tab.charts.append(
                    ChartTjm(
                        count=count,
                        section=section,
                        direction=direction,
                        start=start,
                        end=end,
                    ).get_div()
                )

        tab.chartList.addItem(QListWidgetItem("Par TJM total"))
        tab.charts.append(
            ChartTjm(
                count=count,
                section=section,
                start=start,
                end=end,
            ).get_div()
        )

        self.layers.select_and_zoom_on_section_of_count(count.id)
        if tab.chartList.currentRow() == 0:
            self.chart_selection_changed(0)
        else:
            tab.chartList.setCurrentRow(0)

        QgsMessageLog.logMessage(
            "{} - Debug_GL: Graphique terminé".format(datetime.now()),
            "Comptages",
            Qgis.Info,
        )

    def chart_selection_changed(self, row):
        tab = self.tabWidget.currentWidget()
        tab.webView.setHtml(tab.charts[row])

    def current_tab_changed(self, index: int):
        tab = self.tabWidget.currentWidget()
        if tab.chartList.currentRow() == 0:
            self.chart_selection_changed(0)

    def set_dates(self):
        assert self.count
        self._create_tabs(self.count)

        qs = models.CountDetail.objects.filter(
            id_count=self.count,
        )

        start = self.startDate.date().toPyDate()
        if not start == qs.earliest("timestamp").timestamp.date():
            self.startDate.setStyleSheet("background-color:orange;")
        else:
            self.startDate.setStyleSheet("background-color:white;")

        end = self.endDate.date().toPyDate()
        if not end == qs.latest("timestamp").timestamp.date():
            self.endDate.setStyleSheet("background-color:orange;")
        else:
            self.endDate.setStyleSheet("background-color:white;")

    def reset_dates(self):
        qs = models.CountDetail.objects.filter(
            id_count=self.count,
        )

        self.startDate.setDateTime(qs.earliest("timestamp").timestamp)
        self.endDate.setDateTime(qs.latest("timestamp").timestamp)

        self.startDate.setStyleSheet("background-color:white;")
        self.endDate.setStyleSheet("background-color:white")

        assert self.count
        self._create_tabs(self.count)

    def validate_count(self, section):
        QgsMessageLog.logMessage(
            "{} - Accept data started".format(datetime.now()), "Comptages", Qgis.Info
        )

        tab = self.tabWidget.currentWidget()

        # Currently displayed dates
        # start = self.startDate.date().toPyDate()
        # end = self.endDate.date().toPyDate() + timedelta(days=1)

        assert self.count
        start = self.count.start_process_date
        end = self.count.end_process_date + timedelta(days=1)

        qs = models.CountDetail.objects.filter(
            id_count=self.count,
            id_lane__id_section=section,
            timestamp__gte=start,
            timestamp__lt=end,
        )

        qs.update(import_status=definitions.IMPORT_STATUS_DEFINITIVE)

        # Delete not imported data of the count
        models.CountDetail.objects.filter(
            id_count=self.count,
            import_status=definitions.IMPORT_STATUS_QUARANTINE,
            id_lane__id_section=section,
        ).delete()

        # Calculate tjm of count
        df, tjm = statistics.get_day_data(
            self.count,
            section=None,
            status=definitions.IMPORT_STATUS_DEFINITIVE,
            exclude_trash=True,
        )

        self.count.tjm = tjm
        self.count.save(update_fields=["tjm"])

        self.show_next_quarantined_chart()

        QgsMessageLog.logMessage(
            "{} - Accept data ended".format(datetime.now()), "Comptages", Qgis.Info
        )

    def refuse_count(self, section):
        QgsMessageLog.logMessage(
            "{} - Reject data started".format(datetime.now()), "Comptages", Qgis.Info
        )

        tab = self.tabWidget.currentWidget()

        start = self.startDate.date().toPyDate()
        end = self.endDate.date().toPyDate() + timedelta(days=1)

        models.CountDetail.objects.filter(
            id_count=self.count,
            import_status=definitions.IMPORT_STATUS_QUARANTINE,
            id_lane__id_section=section,
            timestamp__gte=start,
            timestamp__lt=end,
        ).delete()

        self.show_next_quarantined_chart()

        QgsMessageLog.logMessage(
            "{} - Reject data ended".format(datetime.now()), "Comptages", Qgis.Info
        )

    def show_next_quarantined_chart(self):
        QgsMessageLog.logMessage(
            "{} - Generate validation chart started".format(datetime.now()),
            "Comptages",
            Qgis.Info,
        )

        quarantined_counts = models.Count.objects.filter(
            countdetail__import_status=definitions.IMPORT_STATUS_QUARANTINE
        ).distinct()
        if not quarantined_counts.exists():
            self.hide()
            push_info("Il n'y a pas de données à valider")
            QgsMessageLog.logMessage(
                "{} - Generate validation chart ended : No data to validate".format(
                    datetime.now()
                ),
                "Comptages",
                Qgis.Info,
            )
            return

        self.set_attributes(quarantined_counts[0])
        self.show()

        QgsMessageLog.logMessage(
            "{} - Generate validation chart ended".format(datetime.now()),
            "Comptages",
            Qgis.Info,
        )


TAB_CLASS = get_ui_class("chart_tab.ui")


class ChartTab(QTabWidget, TAB_CLASS):
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        self.setupUi(self)
        self.charts = []


class Chart:
    def __init__(self, count, section, lane=None, direction=None, start=None, end=None):
        self.count = count
        self.section = section
        self.lane = lane
        self.direction = direction
        self.start = start
        self.end = end

    def get_div(self):
        pass


class ChartTjm(Chart):
    def get_div(self):
        df, mean = statistics.get_day_data(
            self.count,
            self.section,
            self.lane,
            self.direction,
            start=self.start,
            end=self.end,
            exclude_trash=True,
        )

        if df.empty:
            return

        labels = {"tj": "Véhicules", "date": "Jour", "import_status": "État"}

        fig = px.bar(
            df,
            x="date",
            y="tj",
            title="Véhicules par jour",
            labels=labels,
            color="import_status",
        )

        fig.update_layout(
            xaxis=dict(
                tickmode="auto",
                tickangle=-45,
            )
        )

        fig.add_hline(
            y=mean,
            line_width=3,
            line_dash="dash",
            line_color="red",
            annotation_text=int(mean),
        )
        return plotly.offline.plot(fig, output_type="div")


class ChartTime(Chart):
    def get_div(self):
        df = statistics.get_time_data(
            self.count,
            self.section,
            self.lane,
            self.direction,
            start=self.start,
            end=self.end,
            exclude_trash=True,
        )
        if df.empty:
            return

        title = "Véhicules par heure"
        if self.lane is not None:
            title = "Véhicules par heure, voie {}".format(self.lane.number)
        elif self.direction is not None:
            title = "Véhicules par heure, direction {}".format(self.direction)

        labels = {
            "thm": "Véhicules",
            "date": "Jour",
            "hour": "Heure",
            "import_status": "État",
        }

        fig = px.line(
            df,
            x="hour",
            y="thm",
            color="date",
            render_mode="svg",
            labels=labels,
            line_dash="import_status",
            title=title,
        )

        fig.update_layout(
            xaxis=dict(
                tickmode="array",
                tickvals=[x for x in range(24)],
                ticktext=[f"{x}h-{x+1}h" for x in range(24)],
                tickangle=-45,
            )
        )
        return plotly.offline.plot(fig, output_type="div")


class ChartCat(Chart):
    def get_div(self):
        df_existing = statistics.get_category_data(
            self.count,
            self.section,
            definitions.IMPORT_STATUS_DEFINITIVE,
            start=self.start,
            end=self.end,
        )
        df_new = statistics.get_category_data(
            self.count,
            self.section,
            definitions.IMPORT_STATUS_QUARANTINE,
            start=self.start,
            end=self.end,
        )

        if df_existing.empty and df_new.empty:
            return

        num_of_charts = 0

        if not df_existing.empty:
            num_of_charts += 1

        if not df_new.empty:
            num_of_charts += 1

        specs = [[]]
        for i in range(num_of_charts):
            specs[0].append({"type": "domain"})

        fig = make_subplots(rows=1, cols=num_of_charts, specs=specs)

        if not df_existing.empty:
            fig.add_trace(
                go.Pie(
                    values=df_existing["value"],
                    labels=df_existing["cat_name_code"],
                    textposition="inside",
                    textinfo="label+percent",
                    title="Existant",
                    name="Existant",
                ),
                1,
                1,
            )

        if not df_new.empty:
            fig.add_trace(
                go.Pie(
                    values=df_new["value"],
                    labels=df_new["cat_name_code"],
                    textposition="inside",
                    textinfo="label+percent",
                    title="Nouveau",
                    name="Nouveau",
                ),
                1,
                num_of_charts,
            )

        fig.update_traces(hoverinfo="label+percent+name+value")
        fig.update_layout(title_text="Véhicules groupés par catégorie")

        return plotly.offline.plot(fig, output_type="div")


class ChartSpeed(Chart):
    def get_div(self):
        df = statistics.get_speed_data(
            self.count,
            self.section,
            exclude_trash=True,
            start=self.start,
            end=self.end,
        )
        if df.empty:
            return

        labels = {"times": "Véhicules", "bins": "Vitesse", "import_status": "État"}

        fig = px.bar(
            df,
            x="speed",
            y="times",
            title="Véhicules groupés par vitesse",
            text="times",
            labels=labels,
            barmode="group",
            color="import_status",
        )

        return plotly.offline.plot(fig, output_type="div")
