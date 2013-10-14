# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.conf import settings
from django.db import models


user_model = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Goal'
        db.create_table('splango_goal', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('splango', ['Goal'])

        # Adding model 'Subject'
        db.create_table('splango_subject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('registered_as', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[user_model], unique=True, null=True)),

        ))
        db.send_create_signal('splango', ['Subject'])

        # Adding model 'GoalRecord'
        db.create_table('splango_goalrecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('goal', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['splango.Goal'])),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['splango.Subject'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('req_HTTP_REFERER', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('req_REMOTE_ADDR', self.gf('django.db.models.fields.IPAddressField')(max_length=15, blank=True)),
            ('req_path', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('extra', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('splango', ['GoalRecord'])

        # Adding unique constraint on 'GoalRecord', fields ['subject', 'goal']
        db.create_unique('splango_goalrecord', ['subject_id', 'goal_id'])

        # Adding model 'Enrollment'
        db.create_table('splango_enrollment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['splango.Subject'])),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['splango.Experiment'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('variant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['splango.Variant'])),
        ))
        db.send_create_signal('splango', ['Enrollment'])

        # Adding unique constraint on 'Enrollment', fields ['subject', 'experiment']
        db.create_unique('splango_enrollment', ['subject_id', 'experiment_id'])

        # Adding model 'Experiment'
        db.create_table('splango_experiment', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('splango', ['Experiment'])

        # Adding model 'ExperimentReport'
        db.create_table('splango_experimentreport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['splango.Experiment'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('funnel', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('splango', ['ExperimentReport'])

        # Adding model 'Variant'
        db.create_table('splango_variant', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('experiment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='variants', to=orm['splango.Experiment'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
        ))
        db.send_create_signal('splango', ['Variant'])


    def backwards(self, orm):
        # Removing unique constraint on 'Enrollment', fields ['subject', 'experiment']
        db.delete_unique('splango_enrollment', ['subject_id', 'experiment_id'])

        # Removing unique constraint on 'GoalRecord', fields ['subject', 'goal']
        db.delete_unique('splango_goalrecord', ['subject_id', 'goal_id'])

        # Deleting model 'Goal'
        db.delete_table('splango_goal')

        # Deleting model 'Subject'
        db.delete_table('splango_subject')

        # Deleting model 'GoalRecord'
        db.delete_table('splango_goalrecord')

        # Deleting model 'Enrollment'
        db.delete_table('splango_enrollment')

        # Deleting model 'Experiment'
        db.delete_table('splango_experiment')

        # Deleting model 'ExperimentReport'
        db.delete_table('splango_experimentreport')

        # Deleting model 'Variant'
        db.delete_table('splango_variant')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        user_model: {
            'Meta': {'object_name': user_model.split('.')[1]},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'splango.enrollment': {
            'Meta': {'unique_together': "(('subject', 'experiment'),)", 'object_name': 'Enrollment'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['splango.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['splango.Subject']"}),
            'variant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['splango.Variant']"})
        },
        'splango.experiment': {
            'Meta': {'object_name': 'Experiment'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'primary_key': 'True'})
        },
        'splango.experimentreport': {
            'Meta': {'object_name': 'ExperimentReport'},
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['splango.Experiment']"}),
            'funnel': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'splango.goal': {
            'Meta': {'object_name': 'Goal'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'primary_key': 'True'})
        },
        'splango.goalrecord': {
            'Meta': {'unique_together': "(('subject', 'goal'),)", 'object_name': 'GoalRecord'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'extra': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'goal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['splango.Goal']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'req_HTTP_REFERER': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'req_REMOTE_ADDR': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'blank': 'True'}),
            'req_path': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['splango.Subject']"})
        },
        'splango.subject': {
            'Meta': {'object_name': 'Subject'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'goals': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['splango.Goal']", 'through': "orm['splango.GoalRecord']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'registered_as': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['%s']" % user_model, 'unique': 'True', 'null': 'True'})
        },
        'splango.variant': {
            'Meta': {'object_name': 'Variant'},
            'experiment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variants'", 'to': "orm['splango.Experiment']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'})
        }
    }

    complete_apps = ['splango']