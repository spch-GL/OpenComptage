import plotly
import plotly.graph_objs as go
from datetime import datetime

from qgis.PyQt.QtWidgets import QDockWidget, QListWidgetItem
from comptages.core.utils import get_ui_class
from comptages.ui.resources import *


FORM_CLASS = get_ui_class('chart_dock.ui')


class ChartDock(QDockWidget, FORM_CLASS):

    CHART_TYPE_TIME = 0
    CHART_TYPE_CATEGORY = 1
    CHART_TYPE_SPEED = 2

    def __init__(self, iface, layers, parent=None):
        QDockWidget.__init__(self, parent)
        self.setupUi(self)
        self.layers = layers
        self.count_id = None
        self.status = self.layers.IMPORT_STATUS_DEFINITIVE
        self.chartList.currentRowChanged.connect(self.chart_list_changed)
        self.buttonValidate.clicked.connect(self.validate_count)
        self.buttonRefuse.clicked.connect(self.refuse_count)

    def set_attributes(self, count_id, approval_process=False):
        self.rows = []  # List of tuples chart type, index

        # Remove previous items
        self.chartList.currentRowChanged.disconnect(self.chart_list_changed)
        for i in range(self.chartList.count()):
            self.chartList.takeItem(0)
        self.chartList.currentRowChanged.connect(self.chart_list_changed)

        # TODO build hours chart items based on the lanes and directions.
        lanes = self.layers.get_lanes_of_count(count_id)
        for i, lane in enumerate(lanes):
            self.chartList.addItem(QListWidgetItem('Par heure, {}'.format(i)))
            self.rows.append((self.CHART_TYPE_TIME, lane.attribute('id')))

        self.chartList.addItem(QListWidgetItem('Par catégorie'))
        self.rows.append((self.CHART_TYPE_CATEGORY, 0))
        self.chartList.addItem(QListWidgetItem('Par vitesse'))
        self.rows.append((self.CHART_TYPE_SPEED, 0))

        self.count_id = count_id
        self.setWindowTitle("Comptage: {}, installation: {}".format(
            count_id, self.layers.get_installation_name_of_count(count_id)))
        if approval_process:
            self.buttonValidate.show()
            self.buttonRefuse.show()
            self.status = self.layers.IMPORT_STATUS_QUARANTINE
        else:
            self.buttonValidate.hide()
            self.buttonRefuse.hide()
            self.status = self.layers.IMPORT_STATUS_DEFINITIVE

        self.layers.select_and_zoom_on_section_of_count(count_id)
        if self.chartList.currentRow() == 0:
            self.chart_list_changed(0)
        else:
            self.chartList.setCurrentRow(0)

    def chart_list_changed(self, row):
        print('row: {}'.format(row))
        print('rows[row]: {}'.format(self.rows[row]))
        is_aggregate = self.layers.is_data_aggregate(self.count_id)
        is_detail = self.layers.is_data_detail(self.count_id)
        if self.rows[row][0] == self.CHART_TYPE_TIME:
            lane_or_direction = self.rows[row][1]
            if is_aggregate:
                xs, ys, days = self.layers.get_aggregate_time_chart_data(
                    self.count_id, self.status, lane_or_direction)
            elif is_detail:
                xs, ys, days = self.layers.get_detail_time_chart_data(
                    self.count_id, self.status, lane_or_direction)
            else:
                xs = []
                ys = []
                days = []
            self.plot_chart_time(xs, ys, days)
        elif self.rows[row][0] == self.CHART_TYPE_CATEGORY:
            if is_aggregate:
                labels, values = self.layers.get_aggregate_category_chart_data(
                    self.count_id, self.status)
            elif is_detail:
                labels, values = self.layers.get_detail_category_chart_data(
                    self.count_id, self.status)
            else:
                labels = []
                values = []
            self.plot_chart_category(labels, values)
        elif self.rows[row][0] == self.CHART_TYPE_SPEED:
            if is_aggregate:
                x, y = self.layers.get_aggregate_speed_chart_data(
                    self.count_id, self.status)
            elif is_detail:
                x, y = self.layers.get_detail_speed_chart_data(
                    self.count_id, self.status)
            else:
                x = []
                y = []
            self.plot_chart_speed(x, y)

    def plot_chart_time(self, xs, ys, days):
        data = []
        # In reverse order so if the first day is not complete, the
        # missing hours are added at the beginning of the chart
        for i in range(len(xs)-1, -1, -1):
            day = datetime.strptime(
                days[i], '%Y-%m-%d %H:%M:%S').strftime('%a %d.%m.%Y')
            data.append(
                go.Scatter(
                    x=xs[i],
                    y=ys[i],
                    name=day,
                    showlegend=True
                )
            )

        layout = go.Layout(
            title='Véhicules par heure',
            xaxis=dict(tickangle=-45),
            barmode='group'
        )

        fig = go.Figure(data=data, layout=layout)
        div = plotly.offline.plot(fig, output_type='div')

        self.webView.setHtml(div)

    def plot_chart_speed(self, x, y):

        total_y = sum(y)
        percent_y = ['{}%'.format(round((i / total_y) * 100, 2)) for i in y]

        bar = go.Bar(
            x=x,
            y=y,
            text=percent_y,
            textposition='auto'
        )

        layout = go.Layout(
            title='Véhicules groupés par vitesse')
        fig = go.Figure(data=[bar], layout=layout)
        div = plotly.offline.plot(fig, output_type='div')

        self.webView.setHtml(div)

    def plot_chart_category(self, labels, values):
        pie = go.Pie(labels=labels, values=values)

        layout = go.Layout(title="Véhicules groupés par catégorie")
        fig = go.Figure(data=[pie], layout=layout)
        div = plotly.offline.plot(fig, output_type='div')

        self.webView.setHtml(div)

    def validate_count(self):
        self.layers.change_status_of_count_data(
            self.count_id, self.layers.IMPORT_STATUS_DEFINITIVE)
        self.show_next_quarantined_chart()

    def refuse_count(self):
        self.layers.delete_count_data(self.count_id)
        self.show_next_quarantined_chart()

    def show_next_quarantined_chart(self):
        quarantined_counts = self.layers.get_quarantined_counts()
        if not quarantined_counts:
            self.hide()
            return

        self.set_attributes(quarantined_counts[0], True)
        self.show()
